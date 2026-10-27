"""Parser registry and routing interface for multi-format document extraction."""

from pathlib import Path
from typing import List, Optional

from src.rag_builder.parsers.base import BaseParser, Document, DocumentChunk, ExtractedImage
from src.rag_builder.parsers.docx_parser import DocxParser
from src.rag_builder.parsers.excel_parser import ExcelParser
from src.rag_builder.parsers.pdf_parser import PDFParser
from src.rag_builder.parsers.pptx_parser import PPTXParser
from src.rag_builder.parsers.text_parser import TextParser


class ParserRegistry:
    """Registry managing available parsers and routing files to their handlers."""

    def __init__(self) -> None:
        self.parsers: List[BaseParser] = [
            PDFParser(),
            DocxParser(),
            PPTXParser(),
            ExcelParser(),
            TextParser(),
        ]

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Find the first matching parser for the target file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def get_parser_for_path(self, file_path: Path) -> Optional[BaseParser]:
        """Alias for get_parser."""
        return self.get_parser(file_path)

    def parse_file(self, file_path: Path, output_image_dir: Optional[Path] = None) -> List[Document]:
        """Parse a single file using the appropriate registered parser."""
        parser = self.get_parser(file_path)
        if parser is None:
            raise ValueError(f"No registered parser supports file: {file_path}")
        return parser.parse(file_path, output_image_dir=output_image_dir)


# Global registry instance
default_registry = ParserRegistry()

__all__ = [
    "BaseParser",
    "Document",
    "DocumentChunk",
    "ExtractedImage",
    "PDFParser",
    "DocxParser",
    "PPTXParser",
    "ExcelParser",
    "TextParser",
    "ParserRegistry",
    "default_registry",
]
