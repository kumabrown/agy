#!/usr/bin/env python3
"""Utility script to render and export Mermaid diagrams as images and update the agy_outputs index.

This script converts Mermaid diagram definitions to PNG (or SVG) files via the
mermaid.ink rendering service using standard library modules (no third-party dependencies).
It automatically enforces workspace naming conventions and updates agy_outputs/README.md.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
from pathlib import Path
import re
import sys
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
    """Find the workspace root directory by locating GEMINI.md or agy_outputs.

    Args:
        start_dir: Optional starting directory. Defaults to current working directory.

    Returns:
        Path to the resolved workspace root.
    """
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "agy_outputs").exists() or (parent / "GEMINI.md").exists():
            return parent
    return current


def sanitize_topic(topic: str) -> str:
    """Sanitize the topic name according to workspace standards.

    Strips parentheses, converts hyphens and spaces to underscores, and removes
    disallowed characters.

    Args:
        topic: Raw topic string.

    Returns:
        Sanitized topic identifier.
    """
    cleaned = topic.strip().strip("()").replace("-", "_").replace(" ", "_")
    cleaned = re.sub(r"[^\w_]", "", cleaned)
    return cleaned or "diagram"


def extract_mermaid_code(raw_input: str) -> str:
    """Extract mermaid code from raw string, stripping markdown fences if present.

    Args:
        raw_input: Raw diagram string or markdown snippet.

    Returns:
        Clean Mermaid diagram definition.
    """
    text = raw_input.strip()
    match = re.search(r"```(?:mermaid)?\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def render_mermaid(
    mermaid_code: str,
    image_format: str = "png",
    timeout: int = 25,
    max_retries: int = 3
) -> bytes:
    """Render Mermaid code into image bytes via mermaid.ink service.

    Args:
        mermaid_code: Raw Mermaid diagram syntax string.
        image_format: Image format, either 'png' or 'svg'.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of request attempts for transient network issues.

    Returns:
        Raw image bytes.

    Raises:
        RuntimeError: If the remote rendering service fails or returns an error.
    """
    import time

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


def update_agy_outputs_index(
    readme_path: Path,
    date_str: str,
    category: str,
    description: str,
    filename: str,
    sub_dir: str = "images"
) -> bool:
    """Update or append an entry in agy_outputs/README.md index table.

    Args:
        readme_path: Path to agy_outputs/README.md.
        date_str: 6-digit date string (YYMMDD).
        category: Category string (e.g., 'image').
        description: Description of the asset.
        filename: Name of the exported file.
        sub_dir: Subdirectory name within agy_outputs (e.g., 'images').

    Returns:
        True if the file was modified, False otherwise.
    """
    if not readme_path.exists():
        print(f"  [!] Index file not found at {readme_path}. Skipping index update.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    link_target = f"{sub_dir}/{filename}"
    new_entry = f"| {date_str} | {category} | {description} | [{filename}]({link_target}) |"

    # Avoid adding duplicate entries for the exact same file
    if f"[{filename}]" in content:
        print(f"  [*] Entry for {filename} already exists in {readme_path.name}.")
        return False

    # Look for the index table header
    table_pattern = r"(##\s*📑\s*자료\s*목록\s*인덱스\s*\(Index\)\s*\n\|[^\n]+\|\n\|[^\n]+\|)"
    match = re.search(table_pattern, content)
    if match:
        header_end = match.end()
        updated_content = content[:header_end] + "\n" + new_entry + content[header_end:]
    else:
        # Fallback to appending at end of file
        updated_content = content.rstrip() + "\n" + new_entry + "\n"

    readme_path.write_text(updated_content, encoding="utf-8")
    print(f"  [+] Registered entry in index: {readme_path}")
    return True


def save_diagram_image(
    mermaid_code: str,
    topic: str,
    description: str | None = None,
    workspace_dir: Path | None = None,
    image_format: str = "png",
    rev: str | None = None,
    no_index: bool = False,
    date_override: str | None = None
) -> Path:
    """Render Mermaid code to an image file, save it to agy_outputs, and update the index.

    Args:
        mermaid_code: Mermaid code string.
        topic: Topic name for file naming.
        description: Optional topic description.
        workspace_dir: Optional workspace root directory.
        image_format: 'png' or 'svg'.
        rev: Optional revision string (e.g. '00', '01').
        no_index: If True, do not modify agy_outputs/README.md.
        date_override: Optional YYMMDD date override.

    Returns:
        Path to the saved image file.
    """
    workspace = (workspace_dir or find_workspace_root()).resolve()
    clean_topic = sanitize_topic(topic)
    date_str = date_override or datetime.now().strftime("%y%m%d")
    fmt = image_format.lower()
    ext = "png" if fmt == "png" else "svg"
    category = "image" if ext == "png" else "plot"
    sub_dir = "images" if ext == "png" else "plots"

    target_dir = workspace / "agy_outputs" / sub_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    if rev:
        rev_str = rev if rev.startswith("rev") else f"rev{rev.zfill(2)}"
        filename = f"{category}_({clean_topic})_{date_str}_{rev_str}.{ext}"
    else:
        filename = f"{category}_({clean_topic})_{date_str}.{ext}"

    output_path = target_dir / filename

    print(f"[*] Rendering diagram '{clean_topic}' to {fmt.upper()}...")
    image_bytes = render_mermaid(mermaid_code, image_format=fmt)
    output_path.write_bytes(image_bytes)
    print(f"  [+] Saved image ({len(image_bytes):,} bytes): {output_path}")

    if not no_index:
        readme_path = workspace / "agy_outputs" / "README.md"
        desc = description or f"{clean_topic} 다이어그램"
        update_agy_outputs_index(readme_path, date_str, category, desc, filename, sub_dir=sub_dir)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render and save Mermaid diagram as image to agy_outputs/images/."
    )
    parser.add_argument("--topic", "-t", required=True, help="Topic name (e.g., 'order_flow').")
    parser.add_argument("--desc", "-d", help="Topic description for index table.")
    parser.add_argument("--code", "-c", help="Inline Mermaid code string.")
    parser.add_argument("--code-file", "-f", type=Path, help="File path containing Mermaid code.")
    parser.add_argument("--workspace-dir", "-w", type=Path, help="Target workspace root directory.")
    parser.add_argument("--format", choices=["png", "svg"], default="png", help="Image format (default: png).")
    parser.add_argument("--rev", help="Revision string (e.g., '00', '01').")
    parser.add_argument("--date", help="Date override in YYMMDD format.")
    parser.add_argument("--no-index", action="store_true", help="Skip updating agy_outputs/README.md.")

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
            workspace_dir=args.workspace_dir,
            image_format=args.format,
            rev=args.rev,
            no_index=args.no_index,
            date_override=args.date,
        )
    except Exception as error:
        print(f"[!] Rendering failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
