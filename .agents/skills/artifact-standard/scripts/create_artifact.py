#!/usr/bin/env python3
"""Utility script to scaffold standardized artifact files and automatically update 00_artifacts/README.md index.

This script enforces the unified workspace naming standard:
[format_tag]_[seq_3digit]_([topic])_[YYMMDD]_rev[NN].md
It auto-increments the 3-digit sequence number per format, defaults revision to rev00,
copies the standard template, injects metadata, and synchronizes 00_artifacts/README.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys

# Ensure UTF-8 output across Windows environments
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


CATEGORY_MAP = {
    "plan": {
        "sub_dir": "plans",
        "template": "template_plan.md",
        "category_name": "plan",
    },
    "walkthrough": {
        "sub_dir": "walkthroughs",
        "template": "template_walkthrough.md",
        "category_name": "walkthrough",
    },
    "report": {
        "sub_dir": "reports",
        "template": "template_report.md",
        "category_name": "report",
    },
}


def find_workspace_root(start_dir: Path | None = None) -> Path:
    """Locate the workspace root directory by looking for GEMINI.md or 00_artifacts."""
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "00_artifacts").exists() or (parent / "GEMINI.md").exists():
            return parent
    return current


def sanitize_topic(topic: str) -> str:
    """Sanitize the topic name according to workspace standards (underscores only)."""
    cleaned = topic.strip().strip("()").replace("-", "_").replace(" ", "_")
    cleaned = re.sub(r"[^\w_]", "", cleaned)
    return cleaned or "task"


def get_next_sequence(target_dir: Path, category_name: str) -> str:
    """Scan target_dir for existing files and determine the next 3-digit sequence number."""
    if not target_dir.exists():
        return "001"

    pattern = re.compile(rf"^{re.escape(category_name)}_(\d{{3}})_\(")
    max_seq = 0
    for file_path in target_dir.glob(f"{category_name}_*.md"):
        match = pattern.match(file_path.name)
        if match:
            seq_num = int(match.group(1))
            if seq_num > max_seq:
                max_seq = seq_num
    return f"{max_seq + 1:03d}"


def format_seq(seq: str | int) -> str:
    """Format sequence into a 3-digit zero-padded string."""
    cleaned = re.sub(r"\D", "", str(seq))
    num = int(cleaned) if cleaned else 1
    return f"{num:03d}"


def format_rev(rev: str | int) -> str:
    """Format revision into 'revNN' format."""
    cleaned = str(rev).lower().strip()
    if cleaned.startswith("rev"):
        cleaned = cleaned[3:]
    cleaned = re.sub(r"\D", "", cleaned)
    num = int(cleaned) if cleaned else 0
    return f"rev{num:02d}"


def update_artifacts_index(
    readme_path: Path,
    date_str: str,
    category: str,
    seq_str: str,
    topic: str,
    description: str,
    filename: str,
    sub_dir: str,
    status: str = "Final",
) -> bool:
    """Update or append an entry to the 00_artifacts/README.md index table."""
    if not readme_path.exists():
        print(f"  [!] Index file not found at {readme_path}. Skipping index update.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    link_target = f"{sub_dir}/{filename}"

    # Avoid duplicate entry for the exact same file
    if f"[{filename}]" in content:
        print(f"  [*] Entry for {filename} already exists in {readme_path.name}.")
        return False

    # Determine table column layout in README.md
    if "| 상태 |" in content:
        new_entry = f"| {date_str} | {category} ({seq_str}) | [{filename}]({link_target}) | {description} | {status} |"
    else:
        new_entry = f"| {date_str} | {category} ({seq_str}) | {topic} | {description} | [{filename}]({link_target}) |"

    # Search for index table header
    table_pattern = r"(##\s*📑\s*아티팩트\s*통합\s*인덱스\s*\(Index\)\s*\n\|[^\n]+\|\n\|[^\n]+\|)"
    match = re.search(table_pattern, content)
    if match:
        header_end = match.end()
        updated_content = content[:header_end] + "\n" + new_entry + content[header_end:]
    else:
        updated_content = content.rstrip() + "\n" + new_entry + "\n"

    readme_path.write_text(updated_content, encoding="utf-8")
    print(f"  [+] Registered entry in index: {readme_path}")
    return True


def create_artifact(
    artifact_type: str,
    topic: str,
    description: str,
    workspace_dir: Path | None = None,
    seq: str | None = None,
    rev: str = "00",
    lite: bool = False,
    date_override: str | None = None,
    dry_run: bool = False,
) -> Path | None:
    """Generate a new artifact file from template and update the index table."""
    clean_type = artifact_type.lower().strip()
    if clean_type not in CATEGORY_MAP:
        raise ValueError(f"Invalid artifact type: '{artifact_type}'. Allowed: {list(CATEGORY_MAP.keys())}")

    config = CATEGORY_MAP[clean_type]
    workspace = (workspace_dir or find_workspace_root()).resolve()
    clean_topic = sanitize_topic(topic)

    date_obj = datetime.now()
    date_str = date_override or date_obj.strftime("%y%m%d")
    full_date_str = date_obj.strftime("%Y-%m-%d")

    artifacts_root = workspace / "00_artifacts"
    target_dir = artifacts_root / config["sub_dir"]

    seq_str = format_seq(seq) if seq is not None else get_next_sequence(target_dir, config["category_name"])
    rev_str = format_rev(rev)

    # Standard template: [포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].md
    filename = f"{config['category_name']}_{seq_str}_({clean_topic})_{date_str}_{rev_str}.md"
    target_file = target_dir / filename

    # Locate template file
    skill_dir = workspace / ".agents" / "skills" / "artifact-standard"
    template_path = skill_dir / "templates" / config["template"]
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found at: {template_path}")

    template_content = template_path.read_text(encoding="utf-8")

    # Metadata replacement
    content = template_content.replace("YYYY-MM-DD", full_date_str)
    content = content.replace("[분석/리서치 주제명을 명사형으로 명확히 작성]", f"{topic} 분석 리포트")
    content = content.replace("[구현/설계 주제명을 명사형으로 명확히 작성]", f"{topic} 구현 계획서")
    content = content.replace("[작업 완료 주제명을 명사형으로 명확히 작성]", f"{topic} 작업 완료 보고서")

    if lite:
        content = content.replace("Standard (전체 분석)", "Lightweight (소규모 경량 분석)")
        content = content.replace("Standard (전체 계획)", "Lightweight (소규모 경량 계획)")
        content = content.replace("Standard (전체 보고)", "Lightweight (소규모 패치 보고)")

    if dry_run:
        print("[DRY-RUN] Target File:", target_file)
        print(
            "[DRY-RUN] Index Entry:",
            f"| {date_str} | {config['category_name']} ({seq_str}) | [{filename}]({config['sub_dir']}/{filename}) | {description} | Final |",
        )
        return target_file

    target_dir.mkdir(parents=True, exist_ok=True)
    if target_file.exists():
        print(f"  [!] Warning: Target file {target_file} already exists. Skipping overwrite.")
    else:
        target_file.write_text(content, encoding="utf-8")
        print(f"  [+] Created artifact file: {target_file}")

    readme_path = artifacts_root / "README.md"
    update_artifacts_index(
        readme_path=readme_path,
        date_str=date_str,
        category=config["category_name"],
        seq_str=seq_str,
        topic=topic,
        description=description,
        filename=filename,
        sub_dir=config["sub_dir"],
    )

    return target_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold standard markdown artifact ([format]_[seq]_([topic])_[YYMMDD]_rev[NN].md) and register it in 00_artifacts/README.md."
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["plan", "walkthrough", "report"],
        help="Artifact type: plan, walkthrough, or report.",
    )
    parser.add_argument(
        "--topic", "-k",
        required=True,
        help="Topic identifier (e.g. 'auth_refactor', 'battery_cooling').",
    )
    parser.add_argument(
        "--desc", "-d",
        required=True,
        help="Brief description for the README index table.",
    )
    parser.add_argument(
        "--seq", "-s",
        help="3-digit sequence number (e.g. '001'). Auto-increments if omitted.",
    )
    parser.add_argument(
        "--rev", "-r",
        default="00",
        help="Revision number (default: '00' -> rev00).",
    )
    parser.add_argument(
        "--workspace-dir", "-w",
        type=Path,
        help="Workspace root path (defaults to auto-detection).",
    )
    parser.add_argument(
        "--lite",
        action="store_true",
        help="Apply Lightweight mode flag in metadata.",
    )
    parser.add_argument(
        "--date",
        help="Date override in YYMMDD format.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without creating files or modifying README.",
    )

    args = parser.parse_args()

    try:
        result = create_artifact(
            artifact_type=args.type,
            topic=args.topic,
            description=args.desc,
            workspace_dir=args.workspace_dir,
            seq=args.seq,
            rev=args.rev,
            lite=args.lite,
            date_override=args.date,
            dry_run=args.dry_run,
        )
        if result:
            print(f"[SUCCESS] Artifact ready at: {result}")
    except Exception as exc:
        print(f"[ERROR] Failed to scaffold artifact: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
