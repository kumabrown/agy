#!/usr/bin/env python
"""CLI tool for managing isolated RAG targets and catalog."""

import argparse
import logging
from pathlib import Path
import shutil
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

from src.rag_builder.catalog import RAGCatalog
from src.rag_builder.config import RAGConfig, find_workspace_root, sanitize_target_id

logger = logging.getLogger("manage_rag")


def cmd_list(args: argparse.Namespace, catalog: RAGCatalog) -> int:
    targets = catalog.list_targets()
    print("\n" + "=" * 70)
    print(" 📋 등록된 독립 RAG 타깃 목록 (Registered RAG Targets)")
    print("=" * 70)

    if not targets:
        print("  현재 등록된 RAG 타깃이 없습니다. (No targets registered)")
        print("  새 타깃 생성: python scripts/build_rag.py --file [파일명] --target [타깃ID]")
        print("=" * 70 + "\n")
        return 0

    print(f" 총 {len(targets)}개의 독립 타깃이 관리 중입니다:\n")
    for idx, t in enumerate(targets, start=1):
        print(f"[{idx}] 🎯 타깃 ID : {t.target_id}")
        print(f"    • 타깃 명칭 : {t.target_name}")
        print(f"    • 청크 수   : {t.total_chunks:,} 개 | 도면 수: {t.total_images:,} 개")
        print(f"    • 원천 문서 : {', '.join(t.source_files) if t.source_files else 'N/A'}")
        print(f"    • 저장 경로 : {t.storage_path}")
        print(f"    • 갱신 일자 : {t.updated_at[:19]}")
        print("-" * 70)

    print()
    return 0


def cmd_info(args: argparse.Namespace, catalog: RAGCatalog) -> int:
    clean_id = sanitize_target_id(args.target_id)
    target = catalog.get_target(clean_id)
    if not target:
        print(f"\n❌ 타깃 '{clean_id}'을(를) 찾을 수 없습니다.")
        return 1

    manifest = catalog.load_manifest(clean_id)

    print("\n" + "=" * 70)
    print(f" 🔍 타깃 상세 정보: {clean_id}")
    print("=" * 70)
    print(f"• 타깃 명칭   : {target.target_name}")
    print(f"• 상태         : {target.status}")
    print(f"• 설명         : {target.description or '(없음)'}")
    print(f"• 총 청크 수   : {target.total_chunks:,} 개")
    print(f"• 추출 도면 수 : {target.total_images:,} 개")
    print(f"• 생성 일시   : {target.created_at}")
    print(f"• 갱신 일시   : {target.updated_at}")
    print(f"• 저장소 경로 : {target.storage_path}")
    print(f"• 도면 경로   : {target.images_path}")
    print("\n📄 포함된 원천 문서:")
    for s in target.source_files:
        print(f"  - {s}")

    if manifest.get("file_hashes"):
        print("\n🔒 파일 무결성 해시 (SHA-256):")
        for fpath, fhash in manifest["file_hashes"].items():
            print(f"  - {Path(fpath).name}: {fhash[:16]}...")

    print("=" * 70 + "\n")
    return 0


def cmd_delete(args: argparse.Namespace, catalog: RAGCatalog) -> int:
    clean_id = sanitize_target_id(args.target_id)
    target = catalog.get_target(clean_id)
    if not target:
        print(f"\n❌ 삭제할 타깃 '{clean_id}'이(가) 카탈로그에 존재하지 않습니다.")
        return 1

    if not args.yes:
        confirm = input(f"정말로 타깃 '{clean_id}'({target.target_name})을 삭제하시겠습니까? (y/N): ")
        if confirm.lower() != "y":
            print("삭제가 취소되었습니다.")
            return 0

    success = catalog.delete_target(clean_id, delete_storage=True)
    if success:
        print(f"\n✅ 타깃 '{clean_id}'의 벡터 인덱스 및 이미지 자산이 안전하게 삭제되었습니다.")
        return 0
    else:
        print(f"\n❌ 타깃 '{clean_id}' 삭제 중 오류가 발생했습니다.")
        return 1


def cmd_purge_legacy(args: argparse.Namespace, config: RAGConfig) -> int:
    """Purge old unisolated unified chroma, bm25_index.pkl, file_cache.json, and loose images."""
    print("\n" + "=" * 70)
    print(" 🧹 레거시 비격리 인덱스 및 자산 일괄 제거 (Legacy Purge)")
    print("=" * 70)

    legacy_chroma = config.rag_dir / "chroma"
    legacy_bm25 = config.rag_dir / "bm25_index.pkl"
    legacy_cache = config.rag_dir / "file_cache.json"

    items_to_delete = []
    if legacy_chroma.exists():
        items_to_delete.append(legacy_chroma)
    if legacy_bm25.exists():
        items_to_delete.append(legacy_bm25)
    if legacy_cache.exists():
        items_to_delete.append(legacy_cache)

    # Legacy images directly under agy_outputs/images/
    legacy_images = []
    if config.images_dir.exists():
        for p in config.images_dir.glob("*"):
            if p.is_file() and not p.name.startswith("."):
                legacy_images.append(p)

    print(f"발견된 레거시 인덱스 항목: {len(items_to_delete)} 개")
    for item in items_to_delete:
        print(f"  - {item}")
    print(f"발견된 구 비격리 도면 이미지: {len(legacy_images)} 개")

    if not items_to_delete and not legacy_images:
        print("\n✨ 정리할 레거시 파일이 없습니다. 이미 깨끗한 상태입니다.")
        print("=" * 70 + "\n")
        return 0

    if not args.yes:
        confirm = input("\n위 레거시 인덱스 및 이미지를 모두 영구 삭제하시겠습니까? (y/N): ")
        if confirm.lower() != "y":
            print("취소되었습니다.")
            return 0

    for item in items_to_delete:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"  ✅ 삭제 완료: {item.name}")
        except Exception as e:
            print(f"  ❌ 삭제 실패: {item.name} ({e})")

    for img in legacy_images:
        try:
            img.unlink()
        except Exception:
            pass
    print(f"  ✅ 구 비격리 도면 {len(legacy_images)}개 삭제 완료.")

    print("\n🎉 레거시 데이터 정리가 완료되었습니다! 신규 Multi-Target 구조가 준비되었습니다.")
    print("=" * 70 + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Target RAG catalog and target management tool.")
    subparsers = parser.add_subparsers(dest="command", help="Management commands")

    # list
    subparsers.add_parser("list", help="List all registered RAG targets.")

    # info
    p_info = subparsers.add_parser("info", help="Show detailed information for a target.")
    p_info.add_argument("target_id", type=str, help="Target ID to inspect.")

    # delete
    p_del = subparsers.add_parser("delete", help="Delete a target and its storage.")
    p_del.add_argument("target_id", type=str, help="Target ID to delete.")
    p_del.add_argument("-y", "--yes", action="store_true", help="Confirm deletion without prompting.")

    # purge-legacy
    p_purge = subparsers.add_parser("purge-legacy", help="Purge old unisolated unified RAG indexes.")
    p_purge.add_argument("-y", "--yes", action="store_true", help="Confirm purge without prompting.")

    args = parser.parse_args()
    workspace_root = find_workspace_root()
    config = RAGConfig(workspace_root=workspace_root)
    catalog = RAGCatalog(config=config)

    if args.command == "list" or not args.command:
        return cmd_list(args, catalog)
    elif args.command == "info":
        return cmd_info(args, catalog)
    elif args.command == "delete":
        return cmd_delete(args, catalog)
    elif args.command == "purge-legacy":
        return cmd_purge_legacy(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
