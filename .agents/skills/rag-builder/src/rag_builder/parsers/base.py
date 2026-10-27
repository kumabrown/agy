"""Base data structures and parser abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedImage:
    """Metadata and filesystem path of an extracted diagram/image asset."""

    image_path: str
    page_or_slide: str
    caption: str = ""
    source_file: str = ""


@dataclass
class Document:
    """Represents a parsed document containing text, metadata, and extracted assets."""

    content: str
    source_path: str
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_images: List[ExtractedImage] = field(default_factory=list)


@dataclass
class DocumentChunk:
    """Represents a split chunk of a document ready for embedding and retrieval."""

    chunk_id: str
    content: str
    source_path: str
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_or_slide: Optional[str] = None
    section_title: Optional[str] = None
    associated_images: List[str] = field(default_factory=list)


class BaseParser(ABC):
    """Abstract base class for format-specific document parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Return True if this parser supports the given file format."""
        pass

    @abstractmethod
    def parse(self, file_path: Path, output_image_dir: Optional[Path] = None) -> List[Document]:
        """Parse the target file and return structured Document instances."""
        pass
