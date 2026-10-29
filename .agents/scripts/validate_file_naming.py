#!/usr/bin/env python3
"""Antigravity Lifecycle Hook Script for enforcing .agents/rules/file_naming.md.

This script implements:
1. PreToolUse: Blocks write_file calls that violate the standard naming convention.
2. Stop: Scans the 5 numbered directories on agent turn completion and forces continuation if violations exist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

# Ensure UTF-8 across Windows console environments
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Standard naming regex: [포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]
FILE_NAMING_PATTERN = re.compile(
    r"^(?P<tag>[a-z]+)_(?P<seq>\d{3})_\((?P<topic>[a-zA-Z0-9_]+)\)_(?P<date>\d{6})_rev(?P<rev>\d{2})\.(?P<ext>[a-zA-Z0-9]+)$"
)

# Folder-specific allowed tags and extensions
FOLDER_RULES = {
    "00_artifacts/plans": {
        "tags": {"plan"},
        "exts": {"md"},
    },
    "00_artifacts/walkthroughs": {
        "tags": {"walkthrough"},
        "exts": {"md"},
    },
    "00_artifacts/reports": {
        "tags": {"report"},
        "exts": {"md"},
    },
    "00_artifacts/designs": {
        "tags": {"design"},
        "exts": {"md"},
    },
    "01_input_data/01_references": {
        "tags": {"doc", "pdf", "excel", "csv", "txt", "md"},
        "exts": None,
    },
    "02_output_data/00_data": {
        "tags": {"excel", "csv"},
        "exts": None,
    },
    "02_output_data/01_figure": {
        "tags": {"plot", "image", "architecture", "log"},
        "exts": None,
    },
    "02_output_data/02_reports": {
        "tags": {"doc", "ppt", "pdf"},
        "exts": None,
    },
    "03_scripts": {
        "tags": {"py", "jou", "ccl", "sh"},
        "exts": None,
    },
}

EXEMPT_FILENAMES = {"readme.md", ".gitkeep"}


def find_workspace_root() -> Path:
    """Find the workspace root directory (parent of .agents or current dir)."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "GEMINI.md").exists() or (parent / "00_artifacts").exists() or (parent / ".agents").exists():
            return parent
    return current


def normalize_rel_path(raw_path: str, workspace_root: Path) -> Path | None:
    """Resolve raw path relative to the workspace root."""
    try:
        p = Path(raw_path)
        if not p.is_absolute():
            resolved = (workspace_root / p).resolve()
        else:
            resolved = p.resolve()
        return resolved.relative_to(workspace_root)
    except Exception:
        return None


def match_folder_rule(rel_path: Path) -> tuple[str, dict] | None:
    """Match relative path against managed folder rules."""
    posix_path = rel_path.as_posix()
    for folder_prefix, rule in FOLDER_RULES.items():
        if posix_path.startswith(folder_prefix + "/") or posix_path.startswith(folder_prefix + "\\"):
            return folder_prefix, rule
        if posix_path == folder_prefix:
            return folder_prefix, rule

    # Check for RAG database images subfolder: 04_rag_database/<target>/images/...
    if re.match(r"^04_rag_database/[^/]+/images/.*", posix_path):
        return "04_rag_database/images", {"tags": {"image"}, "exts": None}

    return None


def validate_single_file(filename: str, folder_prefix: str, rule: dict) -> tuple[bool, str]:
    """Validate a single filename against the rules. Returns (is_valid, error_reason)."""
    if filename.lower() in EXEMPT_FILENAMES:
        return True, ""

    match = FILE_NAMING_PATTERN.match(filename)
    if not match:
        return False, (
            f"파일명 '{filename}'이 표준 템플릿 [포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자] 형식에 맞지 않습니다. "
            f"(언더스코어 구분자, 소괄호 주제명, 3자리 일련번호, rev00 필수. 예: {list(rule['tags'])[0]}_001_(example)_261029_rev00.ext)"
        )

    tag = match.group("tag")
    ext = match.group("ext").lower()

    if tag not in rule["tags"]:
        return False, (
            f"'{folder_prefix}' 폴더에서는 포맷태그 '{tag}'를 사용할 수 없습니다. "
            f"허용된 태그: {sorted(list(rule['tags']))}"
        )

    if rule.get("exts") and ext not in rule["exts"]:
        return False, (
            f"'{folder_prefix}' 폴더에서는 확장자 '.{ext}'를 사용할 수 없습니다. "
            f"허용된 확장자: {sorted(list(rule['exts']))}"
        )

    return True, ""


def handle_pre_tool_use(payload: dict, workspace_root: Path) -> dict:
    """Evaluate PreToolUse event for write_file."""
    tool_call = payload.get("toolCall", {})
    name = tool_call.get("name")
    args = tool_call.get("args", {})

    if name != "write_file":
        return {"decision": "allow"}

    raw_path = args.get("Path", "")
    if not raw_path:
        return {"decision": "allow"}

    rel_path = normalize_rel_path(raw_path, workspace_root)
    if rel_path is None:
        return {"decision": "allow"}

    # Exemption: external received folder retains raw filenames
    if rel_path.as_posix().startswith("01_input_data/00_received/"):
        return {"decision": "allow"}

    matched = match_folder_rule(rel_path)
    if not matched:
        # Outside managed folders (e.g. .agents/, root GEMINI.md)
        return {"decision": "allow"}

    folder_prefix, rule = matched
    filename = rel_path.name
    is_valid, reason = validate_single_file(filename, folder_prefix, rule)

    if not is_valid:
        return {
            "decision": "deny",
            "reason": f"[.agents/rules/file_naming.md 위반 차단] {reason}",
        }

    return {"decision": "allow"}


def handle_stop(payload: dict, workspace_root: Path) -> dict:
    """Evaluate Stop event by scanning the workspace for any newly created rogue files."""
    termination_reason = payload.get("terminationReason", "")
    # Only enforce when model finished its turn naturally
    if termination_reason not in ("NO_TOOL_CALL", "TERMINAL_STEP_TYPE", ""):
        return {"decision": "allow"}

    violations = []

    for folder_prefix, rule in FOLDER_RULES.items():
        folder_path = workspace_root / Path(folder_prefix)
        if not folder_path.exists():
            continue

        for file_path in folder_path.iterdir():
            if file_path.is_file():
                is_valid, reason = validate_single_file(file_path.name, folder_prefix, rule)
                if not is_valid:
                    violations.append(f"{folder_prefix}/{file_path.name}: {reason}")

    # Also scan RAG database images
    rag_dir = workspace_root / "04_rag_database"
    if rag_dir.exists():
        for target_dir in rag_dir.iterdir():
            images_dir = target_dir / "images"
            if images_dir.exists() and images_dir.is_dir():
                for img_file in images_dir.iterdir():
                    if img_file.is_file():
                        is_valid, reason = validate_single_file(
                            img_file.name, "04_rag_database/images", {"tags": {"image"}, "exts": None}
                        )
                        if not is_valid:
                            violations.append(f"{img_file.relative_to(workspace_root)}: {reason}")

    if violations:
        msg = (
            "[.agents/rules/file_naming.md 규칙 위반 감지] 워크스페이스 내에 표준 명명 규칙을 위반한 파일이 발견되었습니다.\n"
            + "\n".join(f"- {v}" for v in violations[:5])
            + "\n\n즉시 해당 파일명을 표준 규칙([포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자])에 맞게 변경(Rename)하고 README.md 인덱스를 갱신하세요."
        )
        return {
            "decision": "continue",
            "reason": msg,
        }

    return {"decision": "allow"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate file naming conventions via Antigravity hooks.")
    parser.add_argument("--event", required=True, choices=["PreToolUse", "Stop"], help="Hook event type.")
    args = parser.parse_args()

    workspace_root = find_workspace_root()

    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception as exc:
        print(json.dumps({"decision": "allow", "reason": f"Hook parse error: {exc}"}), flush=True)
        return

    if args.event == "PreToolUse":
        response = handle_pre_tool_use(payload, workspace_root)
    elif args.event == "Stop":
        response = handle_stop(payload, workspace_root)
    else:
        response = {"decision": "allow"}

    print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
