"""Vector storage and BM25 lexical inverted index managers."""

import pickle
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from src.rag_builder.config import RAGConfig, default_config
from src.rag_builder.embedder import BGEEmbeddingManager, default_embedder
from src.rag_builder.parsers.base import DocumentChunk


def tokenize_korean_english(text: str) -> List[str]:
    """Tokenizer extracting Korean, English, and numerical alphanumeric tokens."""
    return re.findall(r"[\w]+", text.lower())


class ChromaDBManager:
    """Manages local Chroma vector database storage and queries using LangChain Chroma."""

    def __init__(
        self,
        config: RAGConfig = default_config,
        embedder: Optional[BGEEmbeddingManager] = None,
        collection_name: Optional[str] = None,
        target_config: Optional[Any] = None,
        persist_directory: Optional[Path] = None,
    ) -> None:
        self.config = config
        self.config.ensure_directories()
        self.embedder = embedder or default_embedder
        self.target_config = target_config

        if target_config is not None:
            self.persist_directory = target_config.chroma_dir
            self.collection_name = collection_name or f"col_{target_config.target_id}"
        elif persist_directory is not None:
            self.persist_directory = persist_directory
            self.collection_name = collection_name or "agy_inputs_collection"
        else:
            self.persist_directory = self.config.chroma_dir
            self.collection_name = collection_name or "agy_inputs_collection"

        self._vector_store = None

    def get_vector_store(self):
        """Lazy load or initialize Chroma vector store instance."""
        if self._vector_store is not None:
            return self._vector_store

        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        lc_embeddings = self.embedder.get_langchain_embeddings()

        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=lc_embeddings,
            persist_directory=str(self.persist_directory.resolve()),
        )
        return self._vector_store

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Insert DocumentChunks into Chroma with full metadata and persist to disk."""
        if not chunks:
            return 0

        from langchain_core.documents import Document as LCDocument

        lc_docs: List[LCDocument] = []
        ids: List[str] = []

        for chk in chunks:
            # Flatten metadata ensuring values are primitive for Chroma compatibility
            flat_meta: Dict[str, Any] = {}
            for k, v in chk.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    flat_meta[k] = v
                elif v is None:
                    flat_meta[k] = ""
                else:
                    flat_meta[k] = str(v)

            flat_meta["chunk_id"] = chk.chunk_id
            flat_meta["source_path"] = chk.source_path
            flat_meta["category"] = chk.category
            flat_meta["page_or_slide"] = chk.page_or_slide or ""
            flat_meta["section_title"] = chk.section_title or ""
            flat_meta["associated_images"] = ";".join(chk.associated_images) if chk.associated_images else ""

            lc_docs.append(LCDocument(page_content=chk.content, metadata=flat_meta))
            ids.append(chk.chunk_id)

        store = self.get_vector_store()
        batch_size = 200
        for i in range(0, len(lc_docs), batch_size):
            batch_docs = lc_docs[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            store.add_documents(documents=batch_docs, ids=batch_ids)
            print(f"    - ChromaDB 벡터 저장 진행: {min(i + batch_size, len(lc_docs))}/{len(lc_docs)} 청크 완료")
        return len(chunks)

    def similarity_search(self, query: str, k: int = 5) -> List[DocumentChunk]:
        """Perform dense semantic search and return structured DocumentChunks."""
        store = self.get_vector_store()
        results = store.similarity_search(query, k=k)

        chunks: List[DocumentChunk] = []
        for doc in results:
            meta = dict(doc.metadata)
            chunk_id = meta.get("chunk_id", "unknown")
            source_path = meta.get("source_path", "")
            category = meta.get("category", "")
            page_slide = meta.get("page_or_slide", "")
            section = meta.get("section_title", "")
            imgs_str = meta.get("associated_images", "")
            associated_imgs = [img for img in imgs_str.split(";") if img]

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=doc.page_content,
                    source_path=source_path,
                    category=category,
                    metadata=meta,
                    page_or_slide=page_slide or None,
                    section_title=section or None,
                    associated_images=associated_imgs,
                )
            )
        return chunks

    def get_retriever(self, k: int = 5):
        """Return a LangChain VectorStoreRetriever instance."""
        store = self.get_vector_store()
        return store.as_retriever(search_kwargs={"k": k})


class BM25IndexManager:
    """Manages lexical BM25 keyword inverted index stored on disk."""

    def __init__(
        self,
        config: RAGConfig = default_config,
        target_config: Optional[Any] = None,
        index_path: Optional[Path] = None,
    ) -> None:
        self.config = config
        self.config.ensure_directories()
        self.target_config = target_config

        if target_config is not None:
            self.index_path = target_config.bm25_file
        elif index_path is not None:
            self.index_path = index_path
        else:
            self.index_path = self.config.rag_dir / "bm25_index.pkl"

        self.chunks: List[DocumentChunk] = []
        self.corpus_tokens: List[List[str]] = []
        self._bm25 = None

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """Build BM25 index from document chunks and save to disk."""
        if not chunks:
            return

        from rank_bm25 import BM25Okapi

        self.chunks = chunks
        self.corpus_tokens = [tokenize_korean_english(chk.content) for chk in chunks]
        self._bm25 = BM25Okapi(self.corpus_tokens)

        # Save to disk
        with open(self.index_path, "wb") as f:
            pickle.dump(
                {"chunks": self.chunks, "corpus_tokens": self.corpus_tokens, "bm25": self._bm25},
                f,
            )

    def load_index(self) -> bool:
        """Load stored BM25 index from disk."""
        if not self.index_path.exists():
            return False

        try:
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.chunks = data["chunks"]
                self.corpus_tokens = data["corpus_tokens"]
                self._bm25 = data["bm25"]
            return True
        except Exception:
            return False

    def search(self, query: str, k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Perform lexical keyword search and return (chunk, score) pairs."""
        if self._bm25 is None:
            if not self.load_index():
                return []

        tokens = tokenize_korean_english(query)
        if not tokens or self._bm25 is None:
            return []

        scores = self._bm25.get_scores(tokens)
        scored_pairs = list(enumerate(scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        # Filter out documents with no matching query tokens
        query_token_set = set(tokens)
        filtered_pairs = [
            (idx, float(score))
            for idx, score in scored_pairs
            if any(tok in set(self.corpus_tokens[idx]) for tok in query_token_set)
        ]

        top_k = filtered_pairs[:k]
        return [(self.chunks[idx], score) for idx, score in top_k]
