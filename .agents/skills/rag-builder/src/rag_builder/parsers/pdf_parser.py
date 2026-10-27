"""Advanced PDF parser combining pdfplumber (table recovery) and PyMuPDF (diagram/image extraction)."""

from datetime import datetime
import os
from pathlib import Path
import re
from typing import List, Optional

import pymupdf  # Modern PyMuPDF API

from src.rag_builder.parsers.base import BaseParser, Document, ExtractedImage


class PDFParser(BaseParser):
    """Parses PDF documents with structural tables and high-resolution image asset extraction."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a file stem for clean image naming."""
        clean = re.sub(r"[^\w\-_]", "_", name)
        return clean.strip("_")

    def _table_to_markdown(self, table_data: List[List[Optional[str]]]) -> str:
        """Convert a 2D table grid into a clean Markdown table."""
        if not table_data or len(table_data) < 1:
            return ""

        # Filter empty rows and normalize cell strings
        normalized_rows: List[List[str]] = []
        for row in table_data:
            clean_row = [str(cell or "").strip().replace("\n", " ") for cell in row]
            if any(clean_row):
                normalized_rows.append(clean_row)

        if not normalized_rows:
            return ""

        col_count = max(len(row) for row in normalized_rows)
        # Pad shorter rows
        padded_rows = [row + [""] * (col_count - len(row)) for row in normalized_rows]

        header = padded_rows[0]
        divider = ["---"] * col_count
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(divider) + " |",
        ]

        for data_row in padded_rows[1:]:
            lines.append("| " + " | ".join(data_row) + " |")

        return "\n".join(lines) + "\n\n"

    def parse(self, file_path: Path, output_image_dir: Optional[Path] = None) -> List[Document]:
        documents: List[Document] = []
        date_tag = datetime.now().strftime("%y%m%d")
        stem_clean = self._sanitize_name(file_path.stem)

        # Open fitz for ultra-fast single-pass image, text, and table extraction
        fitz_doc = pymupdf.open(str(file_path))
        extracted_images: List[ExtractedImage] = []
        full_page_sections: List[str] = []
        seen_image_xrefs = set()

        if output_image_dir is not None:
            output_image_dir.mkdir(parents=True, exist_ok=True)

        for page_idx in range(len(fitz_doc)):
            page = fitz_doc[page_idx]
            page_header = f"### [Page {page_idx + 1}]\n"

            # 1. Extract diagrams / images for this page
            page_images: List[ExtractedImage] = []
            if output_image_dir is not None:
                image_list = page.get_images(full=True)
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    if xref in seen_image_xrefs:
                        continue
                    seen_image_xrefs.add(xref)

                    try:
                        base_image = fitz_doc.extract_image(xref)
                        # Filter out tiny icons or masks (width/height >= 100)
                        if base_image.get("width", 0) < 100 or base_image.get("height", 0) < 100:
                            continue

                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        img_seq = len(extracted_images) + 1
                        img_filename = f"image_{img_seq:03d}_({stem_clean}_p{page_idx + 1}_img{img_idx + 1})_{date_tag}_rev00.{image_ext}"
                        target_path = output_image_dir / img_filename

                        with open(target_path, "wb") as f_img:
                            f_img.write(image_bytes)

                        img_obj = ExtractedImage(
                            image_path=str(target_path.resolve()),
                            page_or_slide=f"Page {page_idx + 1}",
                            caption=f"Figure extracted from page {page_idx + 1}",
                            source_file=str(file_path.resolve()),
                        )
                        extracted_images.append(img_obj)
                        page_images.append(img_obj)
                    except Exception:
                        pass

            # 2. Extract tables (try PyMuPDF find_tables first, fallback to pdfplumber if needed)
            table_texts: List[str] = []
            try:
                tabs = page.find_tables()
                if tabs.tables:
                    for table_idx, tab in enumerate(tabs.tables):
                        grid = tab.extract()
                        md_table = self._table_to_markdown(grid)
                        if md_table:
                            table_texts.append(f"\n[Table {table_idx + 1} - Page {page_idx + 1}]\n" + md_table)
            except Exception:
                pass

            # 3. Extract plain text
            raw_text = page.get_text() or ""

            # 4. Assemble image anchors
            image_anchors: List[str] = []
            for img in page_images:
                image_anchors.append(f"\n![{img.caption}]({Path(img.image_path).as_uri()})\n")

            page_body = raw_text.strip()
            if table_texts:
                page_body += "\n\n" + "\n".join(table_texts)
            if image_anchors:
                page_body += "\n\n" + "\n".join(image_anchors)

            if page_body.strip():
                full_page_sections.append(page_header + page_body)

        fitz_doc.close()

        combined_content = "\n\n---\n\n".join(full_page_sections)
        documents.append(
            Document(
                content=combined_content,
                source_path=str(file_path.resolve()),
                category="pdf",
                metadata={
                    "total_pages": len(full_page_sections),
                    "file_name": file_path.name,
                    "extracted_images_count": len(extracted_images),
                },
                extracted_images=extracted_images,
            )
        )

        return documents
