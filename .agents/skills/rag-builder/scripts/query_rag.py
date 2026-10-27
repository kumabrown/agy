#!/usr/bin/env python
"""CLI tool for querying multi-format RAG index with source citations and diagram links."""

import argparse
import json
import logging
from pathlib import Path
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure skill root is in sys.path
SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from src.rag_builder.config import RAGConfig, find_workspace_root
from src.rag_builder.pipeline import RAGPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the multi-format RAG system using hybrid dense + sparse search."
    )
    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        default=None,
        help="Natural language question or search query.",
    )
    parser.add_argument(
        "-q",
        "--query-flag",
        dest="query_flag",
        type=str,
        default=None,
        help="Alternative flag for specifying the search query.",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=5,
        help="Number of relevant document chunks to retrieve (default: 5).",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Query a specific isolated target ID (e.g. fluent_theory_guide).",
    )
    parser.add_argument(
        "--federated",
        "--all",
        action="store_true",
        help="Search across all registered RAG targets using global RRF.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List all registered RAG targets and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON results for programmatic integration.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable detailed debug logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workspace_root = find_workspace_root()
    config = RAGConfig(workspace_root=workspace_root)

    if args.list_targets:
        from src.rag_builder.catalog import RAGCatalog
        catalog = RAGCatalog(config=config)
        targets = catalog.list_targets()
        print(f"\n📋 등록된 RAG 타깃 목록 ({len(targets)}개):")
        for t in targets:
            print(f"  • {t.target_id} ({t.target_name}) - {t.total_chunks:,} chunks, {t.total_images:,} images")
        print()
        return 0

    query_text = args.query or args.query_flag

    if not query_text:
        print("오류: 질문(Query)을 입력해주세요. (예: python scripts/query_rag.py \"형산발전 12호기 복사열전달\")")
        return 1

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    pipeline = RAGPipeline(config=config)

    result = pipeline.query(
        query_text,
        top_k=args.top_k,
        target_id=args.target,
        federated=args.federated,
    )

    if args.json:
        data = {
            "query": result.query,
            "citations": result.citations,
            "associated_images": result.associated_images,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    "source_path": c.source_path,
                    "page_or_slide": c.page_or_slide,
                    "section_title": c.section_title,
                    "category": c.category,
                    "associated_images": c.associated_images,
                }
                for c in result.chunks
            ],
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    print("\n" + "=" * 70)
    print(" 🔎 LangChain · ChromaDB · BGE-M3 하이브리드 RAG 검색 결과")
    print("=" * 70)
    print(f"❓ 질의문: {query_text}")
    print(f"📊 검색된 상위 청크 수: {len(result.chunks)} 개 (Top-{args.top_k} RRF 융합)")
    print("-" * 70)

    if not result.chunks:
        print("⚠️ 일치하는 관련 문서를 찾지 못했습니다. 먼저 'python scripts/build_rag.py'를 실행하여 인덱스를 구축해주세요.")
        print("=" * 70 + "\n")
        return 0

    for idx, chk in enumerate(result.chunks, start=1):
        file_name = chk.metadata.get("file_name", Path(chk.source_path).name)
        loc = []
        if chk.page_or_slide:
            loc.append(chk.page_or_slide)
        if chk.section_title:
            loc.append(chk.section_title)
        loc_str = f" [{', '.join(loc)}]" if loc else ""

        print(f"\n[{idx}] 📄 {file_name}{loc_str}")
        print(f"    • 청크 ID: {chk.chunk_id} | 분류: {chk.category}")

        # Truncate preview if very long
        preview = chk.content.strip()
        lines = preview.splitlines()
        preview_snip = "\n    ".join(lines[:6])
        if len(lines) > 6:
            preview_snip += f"\n    ... (외 {len(lines) - 6}줄 생략)"
        print(f"    • 내용 발췌:\n    {preview_snip}")

        if chk.associated_images:
            for img in chk.associated_images:
                print(f"    🖼️ 인접 도면/차트: {img}")

    print("\n" + "-" * 70)
    citation_block = RAGPipeline.format_citation_block(result)
    print(citation_block)
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
