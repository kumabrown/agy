#!/usr/bin/env python
"""CLI tool for building and incrementally updating multi-format RAG indexes."""

import argparse
import logging
from pathlib import Path
import sys
import time

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
        description="Build multi-format RAG index from 01_input_data/ into 04_rag_database/ (ChromaDB and BM25)."
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force complete rebuild of the index, ignoring the SHA-256 change cache.",
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        default=None,
        help="Filter indexing to a specific subfolder category (e.g. docs, ppt, pdf).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Filter indexing to specific file name or substring.",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default=None,
        help="Specify target ID for isolated storage (e.g. fluent_theory_guide).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Human-readable display name for the target.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List all registered RAG targets and exit.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=12,
        help="Number of CPU threads for PyTorch/embedding inference (default: 12).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable detailed debug logging.",
    )
    return parser.parse_args()


def progress_tracker(file_name: str, current: int, total: int) -> None:
    pct = int((current / total) * 100)
    print(f"  [{current}/{total}] ({pct}%) 파싱 및 인덱싱 처리 중: {file_name}")


def main() -> int:
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("\n" + "=" * 65)
    print(" 🚀 LangChain · ChromaDB · BGE-M3 멀티포맷 RAG 빌더")
    print("=" * 65)

    workspace_root = find_workspace_root()
    config = RAGConfig(workspace_root=workspace_root)
    if hasattr(args, "threads") and args.threads:
        config.cpu_threads = args.threads
    config.ensure_directories()

    if args.list_targets:
        from src.rag_builder.catalog import RAGCatalog
        catalog = RAGCatalog(config=config)
        targets = catalog.list_targets()
        print(f"\n📋 등록된 RAG 타깃 목록 ({len(targets)}개):")
        for t in targets:
            print(f"  • {t.target_id} ({t.target_name}) - {t.total_chunks:,} chunks, {t.total_images:,} images")
        print()
        return 0

    print(f"📁 작업 기준 디렉터리: {workspace_root}")
    print(f"📥 투입 자료 저장소 : {config.input_dir}")
    if args.target:
        target_cfg = config.get_target_config(args.target)
        print(f"🎯 독립 타깃 ID     : {target_cfg.target_id}")
        print(f"💾 독립 벡터 저장소 : {target_cfg.chroma_dir}")
        print(f"🖼️ 독립 도면 저장소 : {target_cfg.images_dir}")
    else:
        print(f"💾 ChromaDB 벡터원장 : {config.chroma_dir}")
        print(f"🖼️ 도면/이미지 저장소 : {config.images_dir}")
    print(f"⚡ 임베딩 모델       : {config.embedding_model_name} (1024차원)")
    print(f"🔄 재빌드 강제 모드  : {'활성화 (전체 재색인)' if args.force else '증분 색인 (변경 파일만)'}")
    print("-" * 65)

    t0 = time.time()
    pipeline = RAGPipeline(config=config)

    print("\n🔍 원천 자료 스캔 및 인덱싱 착수...")
    result = pipeline.build_index(
        force_rebuild=args.force,
        target_category=args.category,
        target_file=args.file,
        target_id=args.target,
        target_name=args.name,
        progress_callback=progress_tracker,
    )
    elapsed = round(time.time() - t0, 2)

    print("\n" + "=" * 65)
    print(" 📊 RAG 인덱스 구축 결과 보고서")
    print("=" * 65)
    print(f"• 스캔된 총 대상 파일 : {result.scanned_files} 개")
    print(f"• 신규/수정 색인 파일 : {result.indexed_files} 개")
    print(f"• 생성된 텍스트 청크  : {result.total_chunks} 개")
    print(f"• 분리 추출된 도면/차트: {result.extracted_images} 개")
    print(f"• 소요 시간           : {elapsed} 초")
    print(f"• 최종 빌드 상태      : {result.status}")

    if result.details:
        print("\n📋 상세 처리 파일 목록:")
        for det in result.details:
            if det.get("status") == "success":
                print(
                    f"  ✅ [{det['category']}] {det['file_name']} "
                    f"➔ 청크 {det['chunks']}개, 도면 {det['images']}개"
                )
            else:
                print(f"  ❌ [{det['category']}] {det['file_name']} ➔ 실패: {det.get('error')}")

    if result.status == "up_to_date":
        print("\n✨ 모든 파일이 최신 상태입니다. (추가된 변경 파일 0개)")
    elif result.status == "indexed":
        print("\n🎉 RAG 인덱스 구축이 성공적으로 완료되었습니다!")

    print("=" * 65 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
