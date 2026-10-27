"""Semantic and structural chunker preserving heading hierarchy, slides, and tabular blocks."""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from src.rag_builder.config import RAGConfig, default_config
from src.rag_builder.parsers.base import Document, DocumentChunk


class SemanticChunker:
    """Splits documents into coherent chunks while preserving section headings and metadata."""

    def __init__(self, config: RAGConfig = default_config) -> None:
        self.config = config
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap

        # Priority delimiters: Headings -> Slides/Pages -> Tables -> Paragraphs -> Sentences
        self.separators = [
            "\n\n---\n\n",
            "\n### [",
            "\n## ",
            "\n# ",
            "\n[Table",
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ]

    def _extract_page_or_slide(self, text: str) -> Optional[str]:
        """Detect slide number or page marker within chunk text."""
        match = re.search(r"\[(Slide\s*\d+|Page\s*\d+|Sheet:\s*[^\]]+)\]", text)
        if match:
            return match.group(1)
        return None

    def _extract_section_title(self, text: str) -> Optional[str]:
        """Detect the nearest markdown heading within chunk text."""
        match = re.search(r"^(?:#{1,4})\s+(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_image_links(self, text: str) -> List[str]:
        """Extract markdown image links embedded in the text."""
        matches = re.findall(r"!\[.*?\]\(([^\)]+)\)", text)
        return [m.strip() for m in matches if m.strip()]

    def _split_text_recursively(
        self, text: str, separators: List[str], chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Recursively split text based on custom delimiters without external dependencies."""
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0] if separators else ""
        rest_seps = separators[1:] if len(separators) > 1 else []

        if sep and sep in text:
            splits = text.split(sep)
            chunks: List[str] = []
            curr_chunk = ""

            for part in splits:
                candidate = (curr_chunk + sep + part) if curr_chunk else part
                if len(candidate) <= chunk_size:
                    curr_chunk = candidate
                else:
                    if curr_chunk.strip():
                        chunks.append(curr_chunk.strip())
                    # If this single part is larger than chunk_size, split further
                    if len(part) > chunk_size and rest_seps:
                        sub_chunks = self._split_text_recursively(
                            part, rest_seps, chunk_size, chunk_overlap
                        )
                        chunks.extend(sub_chunks)
                        curr_chunk = ""
                    else:
                        curr_chunk = part

            if curr_chunk.strip():
                chunks.append(curr_chunk.strip())

            # Apply overlap if requested
            if chunk_overlap > 0 and len(chunks) > 1:
                overlapped: List[str] = [chunks[0]]
                for i in range(1, len(chunks)):
                    prev_tail = chunks[i - 1][-chunk_overlap:]
                    overlapped.append(prev_tail + " ...\n" + chunks[i])
                return overlapped

            return chunks
        elif rest_seps:
            return self._split_text_recursively(text, rest_seps, chunk_size, chunk_overlap)
        else:
            # Hard character cut if no separators match
            return [
                text[i : i + chunk_size].strip()
                for i in range(0, len(text), chunk_size - chunk_overlap)
                if text[i : i + chunk_size].strip()
            ]

    def split_document(self, document: Document) -> List[DocumentChunk]:
        """Split a single Document into structured DocumentChunks with enriched metadata."""
        raw_text = document.content
        if not raw_text.strip():
            return []

        # Try to use LangChain's splitter if installed, otherwise fallback to our robust recursive splitter
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
                is_separator_regex=False,
            )
            raw_chunks = splitter.split_text(raw_text)
        except (ImportError, Exception):
            raw_chunks = self._split_text_recursively(
                raw_text, self.separators, self.chunk_size, self.chunk_overlap
            )

        file_stem = Path(document.source_path).stem
        clean_stem = re.sub(r"[^\w\-]", "_", file_stem)
        chunks: List[DocumentChunk] = []

        last_known_page_or_slide = None
        last_known_section = None

        for idx, text in enumerate(raw_chunks):
            chunk_id = f"{clean_stem}_chk_{idx + 1:04d}"

            # Detect context markers
            page_slide = self._extract_page_or_slide(text)
            if page_slide:
                last_known_page_or_slide = page_slide

            sec_title = self._extract_section_title(text)
            if sec_title:
                last_known_section = sec_title

            image_links = self._extract_image_links(text)

            meta: Dict[str, Any] = {
                "source_path": document.source_path,
                "category": document.category,
                "file_name": Path(document.source_path).name,
                "chunk_index": idx + 1,
                "total_chunks_in_doc": len(raw_chunks),
                "page_or_slide": last_known_page_or_slide or "",
                "section_title": last_known_section or "",
                "has_images": len(image_links) > 0,
                "associated_images": ";".join(image_links) if image_links else "",
            }
            # Merge original document metadata
            meta.update(document.metadata)

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=text,
                    source_path=document.source_path,
                    category=document.category,
                    metadata=meta,
                    page_or_slide=last_known_page_or_slide,
                    section_title=last_known_section,
                    associated_images=image_links,
                )
            )

        return chunks

    def split_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        """Split a batch of Documents into DocumentChunks."""
        all_chunks: List[DocumentChunk] = []
        for doc in documents:
            all_chunks.extend(self.split_document(doc))
        return all_chunks
