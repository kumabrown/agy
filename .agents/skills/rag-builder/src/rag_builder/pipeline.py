"""High-level RAG pipeline orchestrating scanning, parsing, chunking, indexing, and hybrid querying."""

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.rag_builder.catalog import RAGCatalog, default_catalog
from src.rag_builder.chunker import SemanticChunker
from src.rag_builder.config import RAGConfig, TargetConfig, default_config, sanitize_target_id
from src.rag_builder.embedder import BGEEmbeddingManager
from src.rag_builder.parsers import ParserRegistry, default_registry
from src.rag_builder.parsers.base import Document, DocumentChunk
from src.rag_builder.retriever import HybridRetriever, MultiTargetRetriever
from src.rag_builder.scanner import DirectoryScanner, FileInfo
from src.rag_builder.vector_store import BM25IndexManager, ChromaDBManager

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Structured result of index build operation."""

    scanned_files: int
    indexed_files: int
    total_chunks: int
    extracted_images: int
    status: str  # "up_to_date" | "indexed" | "empty"
    details: List[Dict[str, Any]] = field(default_factory=list)
    target_id: Optional[str] = None


@dataclass
class QueryResult:
    """Structured result of hybrid RAG query."""

    query: str
    chunks: List[DocumentChunk]
    citations: List[Dict[str, Any]]
    associated_images: List[str]
    formatted_context: str
    target_id: Optional[str] = None


class RAGPipeline:
    """Orchestrates end-to-end multi-format RAG ingestion, cataloging, and hybrid retrieval."""

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        registry: Optional[ParserRegistry] = None,
        chunker: Optional[SemanticChunker] = None,
        embedder: Optional[BGEEmbeddingManager] = None,
        chroma_manager: Optional[ChromaDBManager] = None,
        bm25_manager: Optional[BM25IndexManager] = None,
        retriever: Optional[HybridRetriever] = None,
        catalog: Optional[RAGCatalog] = None,
        target_id: Optional[str] = None,
    ) -> None:
        self.config = config or default_config
        self.config.ensure_directories()
        self.catalog = catalog or default_catalog
        self.target_id = sanitize_target_id(target_id) if target_id else None
        self.registry = registry or default_registry
        self.scanner = DirectoryScanner(self.config)
        self.chunker = chunker or SemanticChunker(self.config)
        self.embedder = embedder or BGEEmbeddingManager(self.config)

        if self.target_id:
            target_cfg = self.config.get_target_config(self.target_id)
            self.chroma_manager = chroma_manager or ChromaDBManager(
                config=self.config, embedder=self.embedder, target_config=target_cfg
            )
            self.bm25_manager = bm25_manager or BM25IndexManager(
                config=self.config, target_config=target_cfg
            )
        else:
            self.chroma_manager = chroma_manager or ChromaDBManager(
                config=self.config, embedder=self.embedder
            )
            self.bm25_manager = bm25_manager or BM25IndexManager(config=self.config)

        self.retriever = retriever or HybridRetriever(
            config=self.config,
            chroma_manager=self.chroma_manager,
            bm25_manager=self.bm25_manager,
        )
        self.multi_target_retriever = MultiTargetRetriever(
            config=self.config, catalog=self.catalog, embedder=self.embedder
        )

    def build_index(
        self,
        force_rebuild: bool = False,
        target_category: Optional[str] = None,
        target_file: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> IndexingResult:
        """Scan input files, parse multi-format documents, chunk, and index into Chroma and BM25.

        Args:
            force_rebuild: If True, re-parse and re-index all files regardless of cache.
            target_category: Optional category filter (e.g. 'docs', 'pdf', 'ppt').
            target_file: Optional substring filter for specific file names.
            target_id: Optional target ID to isolate storage in agy_outputs/rag/targets/{target_id}/.
            target_name: Optional human-readable display name for the target.
            progress_callback: Optional callback receiving (file_name, current_idx, total_count).

        Returns:
            IndexingResult containing execution metrics.
        """
        self.config.ensure_directories()

        all_scanned = self.scanner.scan_all()
        if not all_scanned:
            logger.info("No supported files found in %s", self.config.input_dir)
            return IndexingResult(
                scanned_files=0,
                indexed_files=0,
                total_chunks=0,
                extracted_images=0,
                status="empty",
                details=[],
            )

        # Determine which files need indexing
        if force_rebuild:
            files_to_index = all_scanned
        else:
            files_to_index, _ = self.scanner.get_incremental_changes()

        if target_category:
            files_to_index = [f for f in files_to_index if f.category.lower() == target_category.lower()]
        if target_file:
            filter_patterns = [pat.strip().lower() for pat in target_file.split(",") if pat.strip()]
            files_to_index = [
                f for f in files_to_index
                if any(pat in Path(f.file_path).name.lower() for pat in filter_patterns)
            ]

        if not files_to_index:
            logger.info("All selected files are up to date. Incremental index build skipped.")
            return IndexingResult(
                scanned_files=len(all_scanned),
                indexed_files=0,
                total_chunks=0,
                extracted_images=0,
                status="up_to_date",
                details=[],
            )

        logger.info(
            "Starting index build for %d files (out of %d scanned)...",
            len(files_to_index),
            len(all_scanned),
        )

        all_new_chunks: List[DocumentChunk] = []
        file_details: List[Dict[str, Any]] = []
        total_extracted_images = 0

        # Current cache mapping
        cache_data = self.scanner.load_cache() if not force_rebuild else {}

        active_target_id = sanitize_target_id(target_id) if target_id else (self.target_id or 'default')
        target_cfg = self.config.get_target_config(active_target_id)
        chroma_mgr = ChromaDBManager(config=self.config, embedder=self.embedder, target_config=target_cfg)
        bm25_mgr = BM25IndexManager(config=self.config, target_config=target_cfg)
        images_dir = target_cfg.images_dir
        images_dir.mkdir(parents=True, exist_ok=True)

        for idx, file_info in enumerate(files_to_index, start=1):
            file_path = Path(file_info.file_path)
            file_name = file_path.name

            if progress_callback:
                progress_callback(file_name, idx, len(files_to_index))

            parser = self.registry.get_parser_for_path(file_path)
            if not parser:
                logger.warning("No parser available for %s", file_name)
                continue

            try:
                # 1. Parse documents and extract tables/images into target-specific images directory
                docs = parser.parse(file_path, output_image_dir=images_dir)

                # Count extracted images embedded
                images_in_file = 0
                for doc in docs:
                    # Look at parser metadata
                    images_in_file += doc.metadata.get("extracted_images_count", 0)

                total_extracted_images += images_in_file

                # 2. Semantic chunking
                doc_chunks = self.chunker.split_documents(docs)
                all_new_chunks.extend(doc_chunks)

                # 3. Add chunks for this file into target ChromaDB
                if doc_chunks:
                    logger.info("Inserting %d chunks for %s into ChromaDB...", len(doc_chunks), file_name)
                    chroma_mgr.add_chunks(doc_chunks)

                    # 4. Update target BM25 lexical index
                    if not bm25_mgr.load_index():
                        bm25_mgr.build_index(doc_chunks)
                    else:
                        combined_chunks = bm25_mgr.chunks + doc_chunks
                        bm25_mgr.build_index(combined_chunks)

                file_details.append(
                    {
                        "file_name": file_name,
                        "category": file_info.category,
                        "documents": len(docs),
                        "chunks": len(doc_chunks),
                        "images": images_in_file,
                        "status": "success",
                    }
                )

                # Update and persist incremental cache immediately per file
                cache_data[file_info.file_path] = file_info.sha256
                self.scanner.save_cache(cache_data)

            except Exception as e:
                logger.error("Failed to parse/chunk %s: %s", file_name, e)
                file_details.append(
                    {
                        "file_name": file_name,
                        "category": file_info.category,
                        "error": str(e),
                        "status": "error",
                    }
                )

        if not all_new_chunks:
            return IndexingResult(
                scanned_files=len(all_scanned),
                indexed_files=0,
                total_chunks=0,
                extracted_images=total_extracted_images,
                status="empty",
                details=file_details,
                target_id=active_target_id,
            )

        # Register target in catalog if active_target_id is present
        if active_target_id:
            human_name = target_name or active_target_id.replace("_", " ").title()
            source_paths = [f.file_path for f in files_to_index]
            self.catalog.register_target(
                target_id=active_target_id,
                target_name=human_name,
                source_files=source_paths,
                total_chunks=len(all_new_chunks),
                total_images=total_extracted_images,
            )
            self.catalog.save_manifest(
                active_target_id,
                {
                    "target_id": active_target_id,
                    "target_name": human_name,
                    "source_files": source_paths,
                    "total_chunks": len(all_new_chunks),
                    "total_images": total_extracted_images,
                    "file_hashes": {f.file_path: f.sha256 for f in files_to_index},
                },
            )

        logger.info(
            "Index build completed: %d files indexed, %d total chunks, %d images extracted for target '%s'.",
            len(files_to_index),
            len(all_new_chunks),
            total_extracted_images,
            active_target_id or "default",
        )

        return IndexingResult(
            scanned_files=len(all_scanned),
            indexed_files=len(files_to_index),
            total_chunks=len(all_new_chunks),
            extracted_images=total_extracted_images,
            status="indexed",
            details=file_details,
            target_id=active_target_id,
        )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        target_id: Optional[str] = None,
        federated: bool = False,
    ) -> QueryResult:
        """Perform hybrid retrieval and construct citations and associated diagram links.

        Args:
            query_text: Natural language user question or keywords.
            top_k: Number of relevant chunks to retrieve.
            target_id: Optional target ID to query a specific isolated target.
            federated: If True, query across all registered active targets in catalog.

        Returns:
            QueryResult containing retrieved chunks, citations, images, and context.
        """
        active_target_id = sanitize_target_id(target_id) if target_id else self.target_id

        if federated:
            chunks = self.multi_target_retriever.retrieve_federated(query_text, k=top_k)
        elif active_target_id:
            chunks = self.multi_target_retriever.retrieve(query_text, target_id=active_target_id, k=top_k)
        else:
            chunks = self.retriever.retrieve(query_text, k=top_k)

        citations: List[Dict[str, Any]] = []
        associated_images: List[str] = []
        context_parts: List[str] = []

        for idx, chk in enumerate(chunks, start=1):
            file_name = chk.metadata.get("file_name", Path(chk.source_path).name)
            page_slide = chk.page_or_slide or chk.metadata.get("page_or_slide", "")
            section = chk.section_title or chk.metadata.get("section_title", "")
            category = chk.category

            loc_str = ""
            if page_slide:
                loc_str += f"[{page_slide}]"
            if section:
                loc_str += f" ({section})"

            citations.append(
                {
                    "rank": idx,
                    "chunk_id": chk.chunk_id,
                    "file_name": file_name,
                    "source_path": chk.source_path,
                    "category": category,
                    "page_or_slide": page_slide,
                    "section_title": section,
                }
            )

            # Collect unique images
            for img in chk.associated_images:
                if img not in associated_images:
                    associated_images.append(img)

            chunk_header = f"### [출처 {idx}] {file_name} {loc_str}".strip()
            context_parts.append(f"{chunk_header}\n{chk.content}")

        formatted_context = "\n\n---\n\n".join(context_parts)

        return QueryResult(
            query=query_text,
            chunks=chunks,
            citations=citations,
            associated_images=associated_images,
            formatted_context=formatted_context,
            target_id=active_target_id,
        )

    @staticmethod
    def format_citation_block(result: QueryResult) -> str:
        """Format markdown citation and diagram link block adhering to project standards."""
        lines: List[str] = []

        if result.associated_images:
            lines.append("📌 **[관련 도면 및 그래프 자산]**")
            for img in result.associated_images:
                img_path = Path(img.replace("file:///", "").replace("file://", ""))
                img_name = img_path.name
                lines.append(f"- 도면/그래프: [{img_name}]({img})")
            lines.append("")

        if result.citations:
            lines.append("📌 **[근거 자료 출처]**")
            for cit in result.citations:
                loc_desc = []
                if cit["page_or_slide"]:
                    loc_desc.append(cit["page_or_slide"])
                if cit["section_title"]:
                    loc_desc.append(cit["section_title"])
                loc_str = f" ({', '.join(loc_desc)})" if loc_desc else ""
                lines.append(f"- {cit['file_name']}{loc_str}")

        return "\n".join(lines)
