"""Directory scanner and SHA-256 incremental cache manager for operational input materials."""

from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.rag_builder.config import RAGConfig, default_config


@dataclass
class FileInfo:
    """Metadata representing a scanned document file."""

    file_path: str
    rel_path: str
    category: str
    size_bytes: int
    mtime: float
    sha256: str
    source_folder: str = ""  # e.g., '00_received', '01_references'


class DirectoryScanner:
    """Scans 01_input_data/ and detects new, modified, and deleted files using SHA-256 hashing."""

    def __init__(self, config: RAGConfig = default_config) -> None:
        self.config = config

    @staticmethod
    def compute_sha256(file_path: Path, chunk_size: int = 65536) -> str:
        """Calculate the SHA-256 hash of a file efficiently in chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_extension_category(self, file_path: Path) -> str:
        """Determine logical document category from file extension."""
        ext = file_path.suffix.lower()
        for cat, exts in self.config.supported_extensions.items():
            if ext in exts:
                return cat
        return "text"

    def scan_all(self, input_dir: Path | None = None) -> List[FileInfo]:
        """Scan all supported files within the input directory recursively."""
        target_dir = input_dir or self.config.input_dir
        if not target_dir.exists():
            return []

        scanned: List[FileInfo] = []

        for root, _, files in os.walk(target_dir):
            root_path = Path(root)
            for file_name in files:
                if file_name.startswith(".") or file_name.startswith("~"):
                    continue

                full_path = root_path / file_name
                if not self.config.is_supported(full_path):
                    continue

                try:
                    stat = full_path.stat()
                    file_hash = self.compute_sha256(full_path)
                    rel_path = str(full_path.relative_to(target_dir))

                    # Determine top-level folder tag (e.g. 00_received, 01_references)
                    parts = full_path.relative_to(target_dir).parts
                    source_folder = parts[0] if len(parts) > 1 else "root"
                    category = self.get_extension_category(full_path)

                    scanned.append(
                        FileInfo(
                            file_path=str(full_path.resolve()),
                            rel_path=rel_path,
                            category=category,
                            size_bytes=stat.st_size,
                            mtime=stat.st_mtime,
                            sha256=file_hash,
                            source_folder=source_folder,
                        )
                    )
                except (PermissionError, FileNotFoundError):
                    continue

        return scanned

    def load_cache(self, cache_file: Path | None = None) -> Dict[str, str]:
        """Load stored file hashes from disk."""
        target_cache = cache_file or self.config.cache_file
        if not target_cache.exists():
            return {}

        try:
            with open(target_cache, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_cache(self, cache_data: Dict[str, str], cache_file: Path | None = None) -> None:
        """Save file hash dictionary to disk."""
        target_cache = cache_file or self.config.cache_file
        target_cache.parent.mkdir(parents=True, exist_ok=True)
        with open(target_cache, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    def get_incremental_changes(
        self, input_dir: Path | None = None
    ) -> Tuple[List[FileInfo], List[str]]:
        """Identify new/modified files and deleted files relative to the cache.

        Returns:
            Tuple[List[FileInfo], List[str]]: (files_to_index, deleted_file_paths)
        """
        all_current = self.scan_all(input_dir)
        old_cache = self.load_cache()

        current_path_map: Dict[str, FileInfo] = {info.file_path: info for info in all_current}
        files_to_index: List[FileInfo] = []

        # Check for new or changed files
        for f_path, info in current_path_map.items():
            if f_path not in old_cache or old_cache[f_path] != info.sha256:
                files_to_index.append(info)

        # Check for deleted files
        deleted_paths: List[str] = [
            old_path for old_path in old_cache if old_path not in current_path_map
        ]

        return files_to_index, deleted_paths
