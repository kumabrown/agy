#!/usr/bin/env python3
"""Utility script to scaffold standardized artifact files and automatically update artifacts/README.md index.

This script enforces workspace naming standards ([category]_([topic])_[YYMMDD].md),
copies the corresponding standard template, injects metadata, and synchronizes the
artifacts/README.md index table.
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
    """Locate the workspace root directory by looking for GEMINI.md or artifacts."""
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "artifacts").exists() or (parent / "GEMINI.md").exists():
            return parent
    return current


def sanitize_topic(topic: str) -> str:
    """Sanitize the topic name according to workspace standards."""
    cleaned = topic.strip().strip("()").replace("-", "_").replace(" ", "_")
    cleaned = re.sub(r"[^\w_]", "", cleaned)
    return cleaned or "task"


def update_artifacts_index(
    readme_path: Path,
    date_str: str,
    category: str,
    topic: str,
    description: str,
    filename: str,
    sub_dir: str
) -> bool:
    """Update or append an entry to the artifacts/README.md index table."""
    if not readme_path.exists():
        print(f"  [!] Index file not found at {readme_path}. Skipping index update.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    link_target = f"{sub_dir}/{filename}"
    new_entry = f"| {date_str} | {category} | {topic} | {description} | [{filename}]({link_target}) |"

    # Avoid duplicate entry for the exact same file
    if f"[{filename}]" in content:
        print(f"  [*] Entry for {filename} already exists in {readme_path.name}.")
        return False

    # Search for index table header
    table_pattern = r"(##\s*📑\s*아티팩트\s*통합\s*인덱스\s*\(Index\)\s*\n\|[^\n]+\|\n\|[^\n]+\|)"
    match = re.search(table_pattern, content)
    if match:
        header_end = match.end()
        updated_content = content[:header_end] + "\n" + new_entry + content[header_end:]
    else:
        # Fallback append at end of file
        updated_content = content.rstrip() + "\n" + new_entry + "\n"

    readme_path.write_text(updated_content, encoding="utf-8")
    print(f"  [+] Registered entry in index: {readme_path}")
    return True


def create_artifact(
    artifact_type: str,
    topic: str,
    description: str,
    workspace_dir: Path | None = None,
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

    filename = f"{config['category_name']}_({clean_topic})_{date_str}.md"
    target_dir = workspace / "artifacts" / config["sub_dir"]
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
        print("[DRY-RUN] Index Entry:", f"| {date_str} | {config['category_name']} | {topic} | {description} | [{filename}]({config['sub_dir']}/{filename}) |")
        return target_file

    target_dir.mkdir(parents=True, exist_ok=True)
    if target_file.exists():
        print(f"  [!] Warning: Target file {target_file} already exists. Skipping overwrite.")
    else:
        target_file.write_text(content, encoding="utf-8")
        print(f"  [+] Created artifact file: {target_file}")

    readme_path = workspace / "artifacts" / "README.md"
    update_artifacts_index(
        readme_path=readme_path,
        date_str=date_str,
        category=config["category_name"],
        topic=topic,
        description=description,
        filename=filename,
        sub_dir=config["sub_dir"]
    )

    return target_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold standard markdown artifact and register it in artifacts/README.md."
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["plan", "walkthrough", "report"],
        help="Artifact type: plan, walkthrough, or report."
    )
    parser.add_argument(
        "--topic", "-k",
        required=True,
        help="Topic identifier (e.g. 'auth_refactor', 'battery_cooling')."
    )
    parser.add_argument(
        "--desc", "-d",
        required=True,
        help="Brief description for the README index table."
    )
    parser.add_argument(
        "--workspace-dir", "-w",
        type=Path,
        help="Workspace root path (defaults to auto-detection)."
    )
    parser.add_argument(
        "--lite",
        action="store_true",
        help="Apply Lightweight mode flag in metadata."
    )
    parser.add_argument(
        "--date",
        help="Date override in YYMMDD format."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without creating files or modifying README."
    )

    args = parser.parse_args()

    try:
        result = create_artifact(
            artifact_type=args.type,
            topic=args.topic,
            description=args.desc,
            workspace_dir=args.workspace_dir,
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
