"""Spreadsheet (.xlsx, .csv) parser converting tabular rows into structured text."""

import csv
from pathlib import Path
from typing import List, Optional

import openpyxl

from src.rag_builder.parsers.base import BaseParser, Document


class ExcelParser(BaseParser):
    """Parses Excel spreadsheets (.xlsx, .xls) and CSV files into structured Markdown tables."""

    def can_parse(self, file_path: Path) -> bool:
        ext = file_path.suffix.lower()
        return ext in {".xlsx", ".xls", ".csv"}

    def _format_markdown_table(self, rows_data: List[List[str]], max_preview_rows: int = 500) -> str:
        """Format 2D cell data into a Markdown table with row limits."""
        if not rows_data:
            return ""

        trimmed_rows = rows_data[:max_preview_rows]
        col_count = max(len(row) for row in trimmed_rows)
        padded_rows = [row + [""] * (col_count - len(row)) for row in trimmed_rows]

        header = padded_rows[0]
        divider = ["---"] * col_count
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(divider) + " |",
        ]
        for data_row in padded_rows[1:]:
            lines.append("| " + " | ".join(data_row) + " |")

        if len(rows_data) > max_preview_rows:
            lines.append(f"\n*(Note: Truncated {len(rows_data) - max_preview_rows} additional rows)*")

        return "\n".join(lines) + "\n\n"

    def _parse_csv(self, file_path: Path) -> str:
        """Parse CSV file with encoding fallback."""
        encodings = ["utf-8", "cp949", "euc-kr", "latin-1"]
        rows_data: List[List[str]] = []

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc, errors="replace") as f:
                    reader = csv.reader(f)
                    rows_data = [row for row in reader if any(cell.strip() for cell in row)]
                break
            except Exception:
                continue

        return self._format_markdown_table(rows_data)

    def _parse_xlsx(self, file_path: Path) -> str:
        """Parse Excel workbook with multiple sheets."""
        wb = openpyxl.load_workbook(str(file_path), data_only=True, read_only=True)
        sheet_sections: List[str] = []

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows_data: List[List[str]] = []

            for row in sheet.iter_rows(values_only=True):
                str_cells = [str(c or "").strip().replace("\n", " ") for c in row]
                if any(str_cells):
                    rows_data.append(str_cells)

            if rows_data:
                section_header = f"### [Sheet: {sheet_name}]\n"
                md_table = self._format_markdown_table(rows_data)
                sheet_sections.append(section_header + md_table)

        wb.close()
        return "\n\n---\n\n".join(sheet_sections)

    def parse(self, file_path: Path, output_image_dir: Optional[Path] = None) -> List[Document]:
        ext = file_path.suffix.lower()
        if ext == ".csv":
            content = self._parse_csv(file_path)
            category = "csv"
        else:
            content = self._parse_xlsx(file_path)
            category = "excel"

        return [
            Document(
                content=content,
                source_path=str(file_path.resolve()),
                category=category,
                metadata={"file_name": file_path.name, "file_type": ext},
            )
        ]
