#!/usr/bin/env python3
"""Utility script to render and export Mermaid diagrams as images and update the 02_output_data index.

This script converts Mermaid diagram definitions to PNG (or SVG) files via the
mermaid.ink rendering service using Python standard library modules (no third-party dependencies).
It automatically enforces workspace naming conventions (.agents/rules/file_naming.md)
and updates 02_output_data/README.md.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

# Ensure UTF-8 encoding across Windows console environments
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


def find_workspace_root(start_dir: Path | None = None) -> Path:
    """Find the workspace root directory by locating GEMINI.md or 02_output_data."""
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "02_output_data").exists() or (parent / "GEMINI.md").exists():
            return parent
    return current


def sanitize_topic(topic: str) -> str:
    """Sanitize the topic name according to workspace standards (underscores only)."""
    cleaned = topic.strip().strip("()").replace("-", "_").replace(" ", "_")
    cleaned = re.sub(r"[^\w_]", "", cleaned)
    return cleaned or "diagram"


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


def get_next_sequence(target_dir: Path, tag: str) -> str:
    """Scan target_dir for existing files matching tag and determine next 3-digit sequence number."""
    if not target_dir.exists():
        return "001"

    pattern = re.compile(rf"^{re.escape(tag)}_(\d{{3}})_\(")
    max_seq = 0
    for file_path in target_dir.glob(f"{tag}_*.*"):
        match = pattern.match(file_path.name)
        if match:
            seq_num = int(match.group(1))
            if seq_num > max_seq:
                max_seq = seq_num
    return f"{max_seq + 1:03d}"


def extract_mermaid_code(raw_input: str) -> str:
    """Extract mermaid code from raw string, stripping markdown fences if present."""
    text = raw_input.strip()
    match = re.search(r"```(?:mermaid)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def render_mermaid(
    mermaid_code: str,
    image_format: str = "png",
    timeout: int = 25,
    max_retries: int = 3,
) -> bytes:
    """Render Mermaid code into image bytes via mermaid.ink service."""
    clean_code = extract_mermaid_code(mermaid_code)
    if not clean_code:
        raise ValueError("Mermaid diagram code is empty.")

    encoded = base64.b64encode(clean_code.encode("utf-8")).decode("ascii")
    if image_format.lower() == "svg":
        url = f"https://mermaid.ink/svg/{encoded}"
    else:
        url = f"https://mermaid.ink/img/{encoded}?type=png"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    request = urllib.request.Request(url, headers=headers)

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                if not data:
                    raise RuntimeError("Received empty response from rendering service.")
                return data
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Mermaid rendering service returned HTTP {error.code}: {error.reason}. Detail: {error_body}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt < max_retries:
                print(f"  [!] Attempt {attempt} failed ({error}). Retrying in 2 seconds...")
                time.sleep(2)
            else:
                break

    raise RuntimeError(
        f"Network error while connecting to rendering service after {max_retries} attempts: {last_error}"
    ) from last_error


def update_output_index(
    readme_path: Path,
    date_str: str,
    seq_str: str,
    description: str,
    filename: str,
    folder_name: str = "01_figure",
) -> bool:
    """Update or append an entry in 02_output_data/README.md index table."""
    if not readme_path.exists():
        print(f"  [!] Index file not found at {readme_path}. Skipping index update.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    link_target = f"{folder_name}/{filename}"
    new_entry = f"| {date_str} | {folder_name} | {seq_str} | {description} | [{filename}]({link_target}) |"

    # Avoid duplicate entry for the exact same file
    if f"[{filename}]" in content:
        print(f"  [*] Entry for {filename} already exists in {readme_path.name}.")
        return False

    # Look for the index table header in 02_output_data/README.md
    table_pattern = r"(##\s*📑\s*산출\s*자료\s*목록\s*인덱스\s*\(Index\)\s*\n\|[^\n]+\|\n\|[^\n]+\|)"
    match = re.search(table_pattern, content)
    if match:
        header_end = match.end()
        updated_content = content[:header_end] + "\n" + new_entry + content[header_end:]
    else:
        updated_content = content.rstrip() + "\n" + new_entry + "\n"

    readme_path.write_text(updated_content, encoding="utf-8")
    print(f"  [+] Registered entry in index: {readme_path}")
    return True


def save_diagram_image(
    mermaid_code: str,
    topic: str,
    description: str | None = None,
    tag: str = "architecture",
    workspace_dir: Path | None = None,
    image_format: str = "png",
    seq: str | None = None,
    rev: str = "00",
    no_index: bool = False,
    date_override: str | None = None,
) -> Path:
    """Render Mermaid code to an image file, save it to 02_output_data/01_figure/, and update index."""
    workspace = (workspace_dir or find_workspace_root()).resolve()
    clean_topic = sanitize_topic(topic)
    date_str = date_override or datetime.now().strftime("%y%m%d")
    fmt = image_format.lower()
    ext = "png" if fmt == "png" else "svg"

    target_dir = workspace / "02_output_data" / "01_figure"
    target_dir.mkdir(parents=True, exist_ok=True)

    seq_str = format_seq(seq) if seq is not None else get_next_sequence(target_dir, tag)
    rev_str = format_rev(rev)

    # Standard template: [포맷태그]_[일련번호]_([주제명])_[YYMMDD]_rev[NN].[확장자]
    filename = f"{tag}_{seq_str}_({clean_topic})_{date_str}_{rev_str}.{ext}"
    output_path = target_dir / filename

    print(f"[*] Rendering diagram '{clean_topic}' to {fmt.upper()} as {filename}...")
    image_bytes = render_mermaid(mermaid_code, image_format=fmt)
    output_path.write_bytes(image_bytes)
    print(f"  [+] Saved image ({len(image_bytes):,} bytes): {output_path}")

    if not no_index:
        readme_path = workspace / "02_output_data" / "README.md"
        desc = description or f"{clean_topic} 다이어그램"
        update_output_index(
            readme_path=readme_path,
            date_str=date_str,
            seq_str=seq_str,
            description=desc,
            filename=filename,
            folder_name="01_figure",
        )

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render and save Mermaid diagram as image to 02_output_data/01_figure/ ([tag]_[seq]_([topic])_[YYMMDD]_rev[NN].[ext])."
    )
    parser.add_argument("--topic", "-t", required=True, help="Topic identifier (e.g., 'order_flow').")
    parser.add_argument("--desc", "-d", help="Topic description for 02_output_data/README.md index table.")
    parser.add_argument(
        "--tag",
        choices=["architecture", "plot", "image"],
        default="architecture",
        help="Format tag (default: 'architecture').",
    )
    parser.add_argument("--seq", "-s", help="3-digit sequence number (e.g. '001'). Auto-increments if omitted.")
    parser.add_argument("--rev", "-r", default="00", help="Revision string (default: '00' -> rev00).")
    parser.add_argument("--code", "-c", help="Inline Mermaid code string.")
    parser.add_argument("--code-file", "-f", type=Path, help="File path containing Mermaid code.")
    parser.add_argument("--workspace-dir", "-w", type=Path, help="Target workspace root directory.")
    parser.add_argument("--format", choices=["png", "svg"], default="png", help="Image format (default: png).")
    parser.add_argument("--date", help="Date override in YYMMDD format.")
    parser.add_argument("--no-index", action="store_true", help="Skip updating 02_output_data/README.md.")

    args = parser.parse_args()

    # Resolve Mermaid code
    if args.code:
        code = args.code
    elif args.code_file:
        if not args.code_file.exists():
            print(f"[!] Error: Code file not found: {args.code_file}", file=sys.stderr)
            sys.exit(1)
        code = args.code_file.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        code = sys.stdin.read()
    else:
        print("[!] Error: Either --code, --code-file, or stdin must be provided.", file=sys.stderr)
        sys.exit(1)

    try:
        save_diagram_image(
            mermaid_code=code,
            topic=args.topic,
            description=args.desc,
            tag=args.tag,
            workspace_dir=args.workspace_dir,
            image_format=args.format,
            seq=args.seq,
            rev=args.rev,
            no_index=args.no_index,
            date_override=args.date,
        )
    except Exception as error:
        print(f"[!] Rendering failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
