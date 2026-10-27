"""RAG Builder package for multi-format engineering materials."""

from src.rag_builder.catalog import RAGCatalog, TargetMetadata, default_catalog
from src.rag_builder.chunker import SemanticChunker
from src.rag_builder.config import RAGConfig, TargetConfig, default_config, sanitize_target_id
from src.rag_builder.embedder import BGEEmbeddingManager, default_embedder
from src.rag_builder.parsers import (
    BaseParser,
    Document,
    DocumentChunk,
    ExtractedImage,
    PDFParser,
    DocxParser,
    PPTXParser,
    ExcelParser,
    TextParser,
    ParserRegistry,
    default_registry,
)
from src.rag_builder.retriever import HybridRetriever, MultiTargetRetriever
from src.rag_builder.pipeline import IndexingResult, QueryResult, RAGPipeline
from src.rag_builder.scanner import DirectoryScanner, FileInfo
from src.rag_builder.vector_store import BM25IndexManager, ChromaDBManager

__version__ = "2.0.0"

__all__ = [
    "RAGConfig",
    "TargetConfig",
    "sanitize_target_id",
    "default_config",
    "RAGCatalog",
    "TargetMetadata",
    "default_catalog",
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
    "DirectoryScanner",
    "FileInfo",
    "SemanticChunker",
    "BGEEmbeddingManager",
    "default_embedder",
    "ChromaDBManager",
    "BM25IndexManager",
    "HybridRetriever",
    "MultiTargetRetriever",
    "RAGPipeline",
    "IndexingResult",
    "QueryResult",
]

