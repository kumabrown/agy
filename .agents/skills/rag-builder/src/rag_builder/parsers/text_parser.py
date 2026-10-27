"""General text parser supporting scripts, journals, logs, and markdown files."""

from pathlib import Path
from typing import List, Optional

from src.rag_builder.parsers.base import BaseParser, Document


class TextParser(BaseParser):
    """Parses plain text files (.txt, .md, .jou, .ccl, .log) with robust encoding detection."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".jou", ".ccl", ".log"}

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, file_path: Path, output_image_dir: Optional[Path] = None) -> List[Document]:
        encodings = ["utf-8", "cp949", "euc-kr", "latin-1"]
        content = ""

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        if not content:
            # Fallback with replacement
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        return [
            Document(
                content=content.strip(),
                source_path=str(file_path.resolve()),
                category="text",
                metadata={"file_name": file_path.name, "char_count": len(content)},
            )
        ]
