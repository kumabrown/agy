"""RAG target catalog manager for isolated multi-target lifecycle management."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional

from src.rag_builder.config import RAGConfig, TargetConfig, default_config, sanitize_target_id

logger = logging.getLogger(__name__)


@dataclass
class TargetMetadata:
    """Metadata describing an isolated document-specific RAG target."""

    target_id: str
    target_name: str
    created_at: str
    updated_at: str
    source_files: List[str]
    total_chunks: int
    total_images: int
    storage_path: str
    images_path: str
    status: str = "active"
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetMetadata":
        return cls(
            target_id=data.get("target_id", ""),
            target_name=data.get("target_name", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            source_files=data.get("source_files", []),
            total_chunks=data.get("total_chunks", 0),
            total_images=data.get("total_images", 0),
            storage_path=data.get("storage_path", ""),
            images_path=data.get("images_path", ""),
            status=data.get("status", "active"),
            description=data.get("description", ""),
        )


class RAGCatalog:
    """Central registry tracking all isolated RAG targets and their lifecycle."""

    def __init__(self, config: Optional[RAGConfig] = None) -> None:
        self.config = config or default_config
        self.config.ensure_directories()
        self.catalog_file = self.config.catalog_file
        self.ensure_gitignore()

    def ensure_gitignore(self) -> None:
        """Create or ensure 04_rag_database/.gitignore excludes heavy binary vector files."""
        gitignore_path = self.config.gitignore_file
        gitignore_content = """# Ignore heavy binary vector database, SQLite, and index files
*/chroma/
*/*.sqlite3
*/*.parquet
*/*.pkl
file_cache.json
*.tmp
"""
        if not gitignore_path.exists():
            try:
                gitignore_path.write_text(gitignore_content, encoding="utf-8")
                logger.info("Created .gitignore at %s", gitignore_path)
            except Exception as e:
                logger.warning("Could not write .gitignore: %s", e)

    def _load_raw(self) -> Dict[str, Any]:
        """Read index_catalog.json from disk."""
        if not self.catalog_file.exists():
            return {
                "updated_at": datetime.now().isoformat(),
                "default_target": "default",
                "targets": {},
            }
        try:
            with open(self.catalog_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to parse catalog file %s: %s", self.catalog_file, e)
            return {
                "updated_at": datetime.now().isoformat(),
                "default_target": "default",
                "targets": {},
            }

    def _save_raw(self, data: Dict[str, Any]) -> None:
        """Write index_catalog.json atomically to disk."""
        data["updated_at"] = datetime.now().isoformat()
        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self.catalog_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.catalog_file)

    def list_targets(self) -> List[TargetMetadata]:
        """Return all registered targets."""
        data = self._load_raw()
        targets_dict = data.get("targets", {})
        result = []
        for tid, tdata in targets_dict.items():
            if "target_id" not in tdata:
                tdata["target_id"] = tid
            result.append(TargetMetadata.from_dict(tdata))
        return sorted(result, key=lambda x: x.target_id)

    def get_target(self, target_id: str) -> Optional[TargetMetadata]:
        """Fetch metadata for a specific target ID."""
        clean_id = sanitize_target_id(target_id)
        data = self._load_raw()
        tdata = data.get("targets", {}).get(clean_id)
        if not tdata:
            return None
        if "target_id" not in tdata:
            tdata["target_id"] = clean_id
        return TargetMetadata.from_dict(tdata)

    def target_exists(self, target_id: str) -> bool:
        """Check if target exists in the catalog."""
        return self.get_target(target_id) is not None

    def register_target(
        self,
        target_id: str,
        target_name: Optional[str] = None,
        source_files: Optional[List[str]] = None,
        total_chunks: int = 0,
        total_images: int = 0,
        description: str = "",
        status: str = "active",
    ) -> TargetMetadata:
        """Create or update a target entry in the central catalog and sync README.md."""
        clean_id = sanitize_target_id(target_id)
        target_cfg = self.config.get_target_config(clean_id)
        target_cfg.ensure_directories()

        data = self._load_raw()
        now = datetime.now().isoformat()

        existing = data.get("targets", {}).get(clean_id)
        created_at = existing.get("created_at", now) if existing else now

        human_name = target_name or clean_id.replace("_", " ").title()

        # Convert source files to relative strings if possible
        normalized_sources = []
        if source_files:
            for s in source_files:
                p = Path(s)
                try:
                    rel = p.relative_to(self.config.workspace_root)
                    normalized_sources.append(str(rel))
                except Exception:
                    normalized_sources.append(str(p))

        meta = TargetMetadata(
            target_id=clean_id,
            target_name=human_name,
            created_at=created_at,
            updated_at=now,
            source_files=normalized_sources,
            total_chunks=total_chunks,
            total_images=total_images,
            storage_path=str(target_cfg.target_dir.relative_to(self.config.workspace_root)),
            images_path=str(target_cfg.images_dir.relative_to(self.config.workspace_root)),
            status=status,
            description=description,
        )

        data.setdefault("targets", {})[clean_id] = meta.to_dict()
        self._save_raw(data)
        self.ensure_gitignore()
        self.sync_readme_table()
        logger.info("Registered RAG target: %s (%s)", clean_id, human_name)
        return meta

    def delete_target(self, target_id: str, delete_storage: bool = True) -> bool:
        """Remove target from catalog, delete its isolated files on disk, and update README.md."""
        clean_id = sanitize_target_id(target_id)
        data = self._load_raw()
        if clean_id not in data.get("targets", {}):
            logger.warning("Target %s not found in catalog.", clean_id)
            return False

        del data["targets"][clean_id]
        self._save_raw(data)

        if delete_storage:
            target_cfg = self.config.get_target_config(clean_id)
            # Entire document RAG directory (chroma, bm25, manifest, images) is self-contained
            if target_cfg.target_dir.exists():
                try:
                    shutil.rmtree(target_cfg.target_dir)
                    logger.info("Deleted target directory: %s", target_cfg.target_dir)
                except Exception as e:
                    logger.error("Failed to delete %s: %s", target_cfg.target_dir, e)

        self.sync_readme_table()
        logger.info("Target %s deleted successfully.", clean_id)
        return True

    def sync_readme_table(self) -> None:
        """Synchronize the targets table in 04_rag_database/README.md with catalog entries."""
        readme_path = self.config.readme_file
        if not readme_path.exists():
            return

        try:
            content = readme_path.read_text(encoding="utf-8")
            table_header_marker = "## 📑 인덱스 타깃 목록 (Index Targets)"
            if table_header_marker not in content:
                return

            targets = self.list_targets()
            rows = [
                "| 타깃 ID | 문서명/설명 | 청크 수 | 임베딩 모델 | 생성일자 | 상태 |",
                "| :--- | :--- | :---: | :---: | :---: | :---: |",
            ]

            if not targets:
                # Keep empty table placeholder
                new_table = "\n".join(rows) + "\n"
            else:
                for t in targets:
                    date_str = t.created_at[:10].replace("-", "")[2:] if t.created_at else ""
                    rows.append(
                        f"| [{t.target_id}]({t.target_id}/) | {t.target_name} | {t.total_chunks:,} | {self.config.embedding_model_name} | {date_str} | {t.status} |"
                    )
                new_table = "\n".join(rows) + "\n"

            # Replace the section after table_header_marker
            parts = content.split(table_header_marker)
            prefix = parts[0] + table_header_marker + "\n\n"
            readme_path.write_text(prefix + new_table, encoding="utf-8")
            logger.info("Synchronized %s with %d targets.", readme_path, len(targets))
        except Exception as e:
            logger.warning("Failed to sync README table: %s", e)

    def save_manifest(self, target_id: str, manifest_data: Dict[str, Any]) -> None:
        """Write manifest.json inside the document-specific directory."""
        clean_id = sanitize_target_id(target_id)
        target_cfg = self.config.get_target_config(clean_id)
        target_cfg.ensure_directories()
        manifest_data["updated_at"] = datetime.now().isoformat()
        with open(target_cfg.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    def load_manifest(self, target_id: str) -> Dict[str, Any]:
        """Read manifest.json from the document-specific directory."""
        clean_id = sanitize_target_id(target_id)
        target_cfg = self.config.get_target_config(clean_id)
        if not target_cfg.manifest_file.exists():
            return {}
        try:
            with open(target_cfg.manifest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


default_catalog = RAGCatalog()
