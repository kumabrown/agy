"""Configuration settings and workspace directory management for RAG Builder."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Set


def find_workspace_root(start_dir: Path | None = None) -> Path:
    """Locate the workspace root directory by searching for 01_input_data, 04_rag_database, GEMINI.md, or .agents."""
    candidates = []
    if start_dir:
        candidates.append(start_dir.resolve())
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parent)

    for base in candidates:
        for parent in [base, *base.parents]:
            if (
                (parent / "01_input_data").exists()
                or (parent / "04_rag_database").exists()
                or (parent / "GEMINI.md").exists()
                or (parent / ".agents").exists()
                or (parent / "agy_inputs").exists()
            ):
                return parent
    return Path.cwd().resolve()


def sanitize_target_id(name: str) -> str:
    """Convert an arbitrary document name, category, or project name into a clean slug."""
    clean = re.sub(r"[^\w\-_]", "_", name.strip())
    clean = re.sub(r"_+", "_", clean).strip("_").lower()
    return clean or "default"


@dataclass
class TargetConfig:
    """Target-specific configuration containing isolated storage paths per document."""

    target_id: str
    base_config: "RAGConfig"
    target_dir: Path = field(init=False)
    chroma_dir: Path = field(init=False)
    bm25_file: Path = field(init=False)
    manifest_file: Path = field(init=False)
    images_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.target_id = sanitize_target_id(self.target_id)
        # Dedicated document directory directly under 04_rag_database/<target_id>/
        self.target_dir = self.base_config.rag_dir / self.target_id
        self.chroma_dir = self.target_dir / "chroma"
        self.bm25_file = self.target_dir / "bm25_index.pkl"
        self.manifest_file = self.target_dir / "manifest.json"
        # Extracted diagram/chart images self-contained inside 04_rag_database/<target_id>/images/
        self.images_dir = self.target_dir / "images"

    def ensure_directories(self) -> None:
        """Create document-specific directories."""
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class RAGConfig:
    """Configuration class holding paths, model names, and chunking parameters."""

    # Workspace Root
    workspace_root: Path = field(default_factory=find_workspace_root)

    # Core Directories
    input_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    rag_dir: Path = field(init=False)
    catalog_file: Path = field(init=False)
    cache_file: Path = field(init=False)
    readme_file: Path = field(init=False)
    gitignore_file: Path = field(init=False)

    # Legacy compatibility fields
    targets_dir: Path = field(init=False)
    chroma_dir: Path = field(init=False)
    images_dir: Path = field(init=False)

    # Embedding Model Settings
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    embedding_device: str = "cpu"
    cpu_threads: int = 12  # Limit PyTorch CPU threads to 12 cores (Balanced Mode)

    # Chunking Parameters
    chunk_size: int = 800
    chunk_overlap: int = 150

    # Supported File Extensions per Category
    supported_extensions: Dict[str, Set[str]] = field(
        default_factory=lambda: {
            "pdf": {".pdf"},
            "docs": {".docx", ".doc"},
            "ppt": {".pptx", ".ppt"},
            "excel": {".xlsx", ".xls"},
            "csv": {".csv"},
            "text": {".txt", ".md", ".jou", ".ccl", ".log"},
        }
    )

    def __post_init__(self) -> None:
        """Resolve paths relative to the workspace root."""
        # 1. Operational Input Directory (01_input_data with fallback to agy_inputs)
        candidate_input = self.workspace_root / "01_input_data"
        self.input_dir = candidate_input if candidate_input.exists() else (self.workspace_root / "agy_inputs")

        # 2. RAG Knowledge Base Directory (04_rag_database with fallback to agy_outputs/rag)
        candidate_rag = self.workspace_root / "04_rag_database"
        if candidate_rag.exists():
            self.rag_dir = candidate_rag
        else:
            self.rag_dir = self.workspace_root / "04_rag_database"

        # 3. Practical Output Directory (02_output_data with fallback to agy_outputs)
        candidate_output = self.workspace_root / "02_output_data"
        self.output_dir = candidate_output if candidate_output.exists() else (self.workspace_root / "agy_outputs")

        # 4. Central Metadata Files
        self.catalog_file = self.rag_dir / "index_catalog.json"
        self.cache_file = self.rag_dir / "file_cache.json"
        self.readme_file = self.rag_dir / "README.md"
        self.gitignore_file = self.rag_dir / ".gitignore"

        # 5. Compatibility Aliases
        self.targets_dir = self.rag_dir
        self.chroma_dir = self.rag_dir
        self.images_dir = self.rag_dir

    def ensure_directories(self) -> None:
        """Ensure that required output and storage directories exist."""
        self.rag_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_target_config(self, target_id: str) -> TargetConfig:
        """Provision an isolated TargetConfig for a given target identifier."""
        cfg = TargetConfig(target_id=target_id, base_config=self)
        cfg.ensure_directories()
        return cfg

    def is_supported(self, file_path: Path) -> bool:
        """Check if a file has a supported extension."""
        ext = file_path.suffix.lower()
        for exts in self.supported_extensions.values():
            if ext in exts:
                return True
        return False


# Global default configuration instance
default_config = RAGConfig()
