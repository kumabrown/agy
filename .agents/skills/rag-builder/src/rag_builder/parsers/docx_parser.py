"""Word document (.docx) parser preserving heading hierarchy and tabular structures."""

from pathlib import Path
from typing import List, Optional

import docx

from src.rag_builder.parsers.base import BaseParser, Document


class DocxParser(BaseParser):
    """Parses Word (.docx) documents preserving heading hierarchy and tabular structures."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".docx"

    def _table_to_markdown(self, table: docx.table.Table) -> str:
        """Convert a docx Table into a clean Markdown table."""
        rows_data: List[List[str]] = []
        for row in table.rows:
            cell_texts = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            # Avoid repeating text in merged cells
            dedup_cells: List[str] = []
            for text in cell_texts:
                if not dedup_cells or text != dedup_cells[-1]:
                    dedup_cells.append(text)
                else:
                    dedup_cells.append("")
            if any(dedup_cells):
                rows_data.append(dedup_cells)

        if not rows_data:
            return ""

        col_count = max(len(row) for row in rows_data)
        padded_rows = [row + [""] * (col_count - len(row)) for row in rows_data]

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
        doc = docx.Document(str(file_path))
        elements: List[str] = []

        # Iterate over body blocks (paragraphs and tables)
        for child in doc.element.body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "p":
                # Find corresponding paragraph
                p_text = child.text.strip() if child.text else ""
                if not p_text:
                    continue

                # Inspect style through docx paragraph wrapper
                # Find matching paragraph object
                for p in doc.paragraphs:
                    if p._element is child:
                        style_name = p.style.name.lower() if p.style and p.style.name else ""
                        if "heading 1" in style_name:
                            elements.append(f"\n# {p.text.strip()}\n")
                        elif "heading 2" in style_name:
                            elements.append(f"\n## {p.text.strip()}\n")
                        elif "heading 3" in style_name:
                            elements.append(f"\n### {p.text.strip()}\n")
                        elif "heading" in style_name:
                            elements.append(f"\n#### {p.text.strip()}\n")
                        else:
                            elements.append(p.text.strip())
                        break

            elif tag == "tbl":
                # Find matching table object
                for tbl in doc.tables:
                    if tbl._element is child:
                        md_tbl = self._table_to_markdown(tbl)
                        if md_tbl:
                            elements.append(f"\n[Table]\n{md_tbl}")
                        break

        # Fallback if body iteration was sparse
        if not elements:
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    style_name = p.style.name.lower() if p.style and p.style.name else ""
                    if "heading 1" in style_name:
                        elements.append(f"\n# {txt}\n")
                    elif "heading 2" in style_name:
                        elements.append(f"\n## {txt}\n")
                    elif "heading 3" in style_name:
                        elements.append(f"\n### {txt}\n")
                    else:
                        elements.append(txt)

            for table in doc.tables:
                md_tbl = self._table_to_markdown(table)
                if md_tbl:
                    elements.append(f"\n[Table]\n{md_tbl}")

        combined_text = "\n\n".join(elements)

        return [
            Document(
                content=combined_text,
                source_path=str(file_path.resolve()),
                category="docs",
                metadata={"file_name": file_path.name, "paragraph_count": len(doc.paragraphs)},
            )
        ]
