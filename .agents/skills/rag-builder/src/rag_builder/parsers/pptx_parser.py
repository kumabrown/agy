"""PowerPoint (.pptx) presentation parser extracting slide titles, body, tables, and notes."""

from pathlib import Path
from typing import List, Optional

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from src.rag_builder.parsers.base import BaseParser, Document


class PPTXParser(BaseParser):
    """Parses PowerPoint (.pptx) presentations preserving slide context and speaker notes."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pptx"

    def _table_to_markdown(self, table) -> str:
        """Convert a pptx table into a clean Markdown table."""
        rows_data: List[List[str]] = []
        for row in table.rows:
            cell_texts = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cell_texts):
                rows_data.append(cell_texts)

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
        prs = Presentation(str(file_path))
        slide_sections: List[str] = []

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_title = ""
            slide_texts: List[str] = []
            slide_tables: List[str] = []

            for shape in slide.shapes:
                if shape.has_text_frame:
                    text = shape.text_frame.text.strip()
                    if not text:
                        continue

                    # Check if shape is likely the slide title
                    if shape == slide.shapes.title or (not slide_title and len(text) < 80 and "\n" not in text):
                        slide_title = text
                    else:
                        slide_texts.append(text)

                elif shape.has_table:
                    md_table = self._table_to_markdown(shape.table)
                    if md_table:
                        slide_tables.append(md_table)

            # Check for speaker notes
            speaker_notes = ""
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()
                if notes_text:
                    speaker_notes = f"\n*Speaker Notes*: {notes_text}"

            # Format the slide section
            title_display = f" - {slide_title}" if slide_title else ""
            section = f"### [Slide {slide_idx}{title_display}]\n"
            if slide_texts:
                section += "\n".join(slide_texts) + "\n"
            if slide_tables:
                section += "\n" + "\n".join(slide_tables)
            if speaker_notes:
                section += speaker_notes + "\n"

            slide_sections.append(section.strip())

        combined_text = "\n\n---\n\n".join(slide_sections)

        return [
            Document(
                content=combined_text,
                source_path=str(file_path.resolve()),
                category="ppt",
                metadata={"total_slides": len(prs.slides), "file_name": file_path.name},
            )
        ]
