#!/usr/bin/env python3
"""Antigravity Lifecycle Hook Script for validating CFD JSON Spec Manifests.

This script enforces deterministic validation for:
02_output_data/00_data/json_[SEQ]_([topic]_spec)_[YYMMDD]_rev[NN].json

Validation rules:
1. Valid JSON syntax.
2. Required immutable core keys:
   - project_meta: topic, solver, time_regime
   - physics_models: energy, turbulence
   - dimensionless_analysis: governing_regime, metrics
   - materials: dict
   - boundary_conditions: dict
   - mesh_strategy: dict
   - target_specs: convergence_criteria with continuity_residual, energy_residual,
     monitor_fluctuation_pct, and conservation_imbalance_pct as {"mass": float, "energy": float}.
   - results_summary: null or dict.
3. Permissive extension rule:
   - Any keys under physics_models.special_models or custom domain fields are 100% allowed.
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


JSON_SPEC_PATTERN = re.compile(
    r"^json_\d{3}_\([a-zA-Z0-9_]+\)_\d{6}_rev\d{2}\.json$"
)


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


def is_json_spec_file(rel_path: Path) -> bool:
    """Check if the relative path points to a managed JSON spec file."""
    posix_path = rel_path.as_posix()
    if not (posix_path.startswith("02_output_data/00_data/") or posix_path.startswith("02_output_data\\00_data\\")):
        return False
    return bool(JSON_SPEC_PATTERN.match(rel_path.name))


def validate_spec_content(content_str: str) -> tuple[bool, str]:
    """Validate JSON spec content against schema rules. Returns (is_valid, error_reason)."""
    try:
        data = json.loads(content_str)
    except Exception as exc:
        return False, f"유효한 JSON 문법이 아닙니다: {exc}"

    if not isinstance(data, dict):
        return False, "JSON 스펙의 최상위는 객체(Dictionary) 형태여야 합니다."

    # 1. Check top-level core keys
    core_keys = [
        "project_meta",
        "physics_models",
        "dimensionless_analysis",
        "materials",
        "boundary_conditions",
        "mesh_strategy",
        "target_specs",
    ]
    for k in core_keys:
        if k not in data:
            return False, f"필수 최상위 키 '{k}'가 누락되었습니다."

    # 2. project_meta checks
    meta = data.get("project_meta")
    if not isinstance(meta, dict):
        return False, "'project_meta'는 객체여야 합니다."
    for req in ["topic", "solver", "time_regime"]:
        if req not in meta:
            return False, f"'project_meta.{req}' 필드가 누락되었습니다."

    # 3. physics_models checks
    phys = data.get("physics_models")
    if not isinstance(phys, dict):
        return False, "'physics_models'는 객체여야 합니다."
    if "energy" not in phys:
        return False, "'physics_models.energy' (bool) 필드가 누락되었습니다."
    if "turbulence" not in phys:
        return False, "'physics_models.turbulence' 필드가 누락되었습니다."

    # 4. dimensionless_analysis checks
    dim = data.get("dimensionless_analysis")
    if not isinstance(dim, dict):
        return False, "'dimensionless_analysis'는 객체여야 합니다."
    if "governing_regime" not in dim:
        return False, "'dimensionless_analysis.governing_regime' 필드가 누락되었습니다."
    if "metrics" not in dim or not isinstance(dim["metrics"], dict):
        return False, "'dimensionless_analysis.metrics' 객체가 누락되었습니다."

    # 5. target_specs & convergence_criteria checks
    ts = data.get("target_specs")
    if not isinstance(ts, dict):
        return False, "'target_specs'는 객체여야 합니다."
    conv = ts.get("convergence_criteria")
    if not isinstance(conv, dict):
        return False, "'target_specs.convergence_criteria' 객체가 누락되었습니다."

    for req_c in ["continuity_residual", "energy_residual", "monitor_fluctuation_pct"]:
        if req_c not in conv:
            return False, f"'target_specs.convergence_criteria.{req_c}' 필드가 누락되었습니다."

    # Critical check: conservation_imbalance_pct must be a dict with mass and energy
    imbalance = conv.get("conservation_imbalance_pct")
    if not isinstance(imbalance, dict):
        return False, (
            "'target_specs.convergence_criteria.conservation_imbalance_pct'는 단일 숫자가 아닌 "
            "{'mass': 0.1, 'energy': 0.5} 형태의 객체여야 합니다."
        )
    if "mass" not in imbalance or "energy" not in imbalance:
        return False, (
            "'conservation_imbalance_pct' 객체 내에 'mass'와 'energy' 허용 오차 한계치가 모두 명시되어야 합니다. "
            "(예: {'mass': 0.1, 'energy': 0.5})"
        )

    # 6. results_summary checks (if populated)
    if "results_summary" in data and data["results_summary"] is not None:
        res = data["results_summary"]
        if not isinstance(res, dict):
            return False, "'results_summary'는 null이거나 객체여야 합니다."
        if "generated_assets" in res and isinstance(res["generated_assets"], dict):
            assets = res["generated_assets"]
            if "flowfield_images" in assets and not isinstance(assets["flowfield_images"], list):
                return False, "'results_summary.generated_assets.flowfield_images'는 이미지 경로 목록(List)이어야 합니다."

    return True, ""


def handle_pre_tool_use(payload: dict, workspace_root: Path) -> dict:
    """PreToolUse hook: intercept write_file on json_*_spec_*.json."""
    tool_call = payload.get("tool_call", {})
    name = tool_call.get("name", "")
    args = tool_call.get("arguments", {})

    if name != "write_file":
        return {"decision": "allow"}

    raw_path = args.get("Path", "")
    if not raw_path:
        return {"decision": "allow"}

    rel_path = normalize_rel_path(raw_path, workspace_root)
    if rel_path is None or not is_json_spec_file(rel_path):
        # Early exit for non-spec files
        return {"decision": "allow"}

    content = args.get("Content", "")
    is_valid, reason = validate_spec_content(content)

    if not is_valid:
        return {
            "decision": "deny",
            "reason": (
                f"[CFD JSON 스펙 하네스 검증 차단] '{rel_path.name}'의 내용이 JSON SSOT 표준 스키마를 위반했습니다.\n"
                f"원인: {reason}\n"
                "해결: .agents/templates/template_catalog.json 및 template_cfd_spec_*.json 구조를 참조하여 스키마를 보정한 뒤 다시 write_file을 호출하십시오."
            ),
        }

    return {"decision": "allow"}


def handle_stop(payload: dict, workspace_root: Path) -> dict:
    """Stop hook: check any newly modified spec files in 02_output_data/00_data."""
    spec_dir = workspace_root / "02_output_data" / "00_data"
    if not spec_dir.exists():
        return {"decision": "allow"}

    violations = []
    for f in spec_dir.glob("json_*_spec_*.json"):
        try:
            content = f.read_text(encoding="utf-8")
            is_valid, reason = validate_spec_content(content)
            if not is_valid:
                violations.append(f"{f.name}: {reason}")
        except Exception as exc:
            violations.append(f"{f.name}: 파일 읽기 오류 ({exc})")

    if violations:
        msg = (
            "[CFD JSON 스펙 하네스 위반 감지] 워크스페이스 내 JSON 스펙 파일에서 규격 위반이 발견되었습니다.\n"
            + "\n".join(f"- {v}" for v in violations[:3])
            + "\n\n즉시 스펙 파일을 표준 스키마에 맞게 수정하십시오."
        )
        return {"decision": "continue", "reason": msg}

    return {"decision": "allow"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CFD JSON Spec Manifests via Antigravity hooks.")
    parser.add_argument("--event", choices=["PreToolUse", "Stop"], help="Hook event type.")
    parser.add_argument("--file", help="Standalone file validation path.")
    args = parser.parse_args()

    workspace_root = find_workspace_root()

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = workspace_root / file_path
        if not file_path.exists():
            print(f"[FAIL] File not found: {file_path}")
            sys.exit(1)
        content = file_path.read_text(encoding="utf-8")
        is_valid, reason = validate_spec_content(content)
        if is_valid:
            print(f"[PASS] {file_path.name} is valid JSON spec.")
            sys.exit(0)
        else:
            print(f"[FAIL] {file_path.name} validation error: {reason}")
            sys.exit(1)

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
