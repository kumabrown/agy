"""Hybrid retriever fusing Dense vector search (Chroma/BGE-M3) and Sparse lexical search (BM25)."""

from typing import Any, Dict, List, Optional, Tuple

from src.rag_builder.config import RAGConfig, default_config
from src.rag_builder.parsers.base import DocumentChunk
from src.rag_builder.vector_store import BM25IndexManager, ChromaDBManager


class HybridRetriever:
    """Ensemble hybrid retriever combining semantic vector similarity and BM25 keyword matching via RRF."""

    def __init__(
        self,
        config: RAGConfig = default_config,
        chroma_manager: Optional[ChromaDBManager] = None,
        bm25_manager: Optional[BM25IndexManager] = None,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
        rrf_constant: int = 60,
    ) -> None:
        self.config = config
        self.chroma_manager = chroma_manager or ChromaDBManager(config)
        self.bm25_manager = bm25_manager or BM25IndexManager(config)
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_constant = rrf_constant

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[DocumentChunk],
        sparse_results: List[Tuple[DocumentChunk, float]],
        k: int = 5,
    ) -> List[DocumentChunk]:
        """Combine dense and sparse ranked lists using Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # 1. Score dense vector results
        for rank, chk in enumerate(dense_results, start=1):
            cid = chk.chunk_id
            chunk_map[cid] = chk
            score = self.dense_weight / (self.rrf_constant + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        # 2. Score sparse BM25 results
        for rank, (chk, _) in enumerate(sparse_results, start=1):
            cid = chk.chunk_id
            chunk_map[cid] = chk
            score = self.sparse_weight / (self.rrf_constant + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        # Sort by combined RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        return [chunk_map[cid] for cid in sorted_cids[:k]]

    def retrieve(self, query: str, k: int = 5) -> List[DocumentChunk]:
        """Perform hybrid search using Chroma Dense + BM25 Sparse with RRF."""
        # 1. Fetch dense candidates (get k*2 for better fusion candidate pool)
        try:
            dense_candidates = self.chroma_manager.similarity_search(query, k=k * 2)
        except Exception:
            dense_candidates = []

        # 2. Fetch sparse candidates
        try:
            sparse_candidates = self.bm25_manager.search(query, k=k * 2)
        except Exception:
            sparse_candidates = []

        # If one source failed or has no results, fallback gracefully
        if not dense_candidates and not sparse_candidates:
            return []
        if not dense_candidates:
            return [chk for chk, _ in sparse_candidates[:k]]
        if not sparse_candidates:
            return dense_candidates[:k]

        # 3. Fuse rankings via RRF
        return self._reciprocal_rank_fusion(dense_candidates, sparse_candidates, k=k)

    def as_langchain_retriever(self, k: int = 5):
        """Return a LangChain BaseRetriever-compatible wrapper for LCEL pipelines."""
        from langchain_core.callbacks import CallbackManagerForRetrieverRun
        from langchain_core.documents import Document as LCDocument
        from langchain_core.retrievers import BaseRetriever

        parent = self

        class _LCHybridRetriever(BaseRetriever):
            def _get_relevant_documents(
                self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
            ) -> List[LCDocument]:
                chunks = parent.retrieve(query, k=k)
                return [LCDocument(page_content=c.content, metadata=dict(c.metadata)) for c in chunks]

        return _LCHybridRetriever()


class MultiTargetRetriever:
    """Manages queries across isolated RAG targets with targeted and federated RRF search."""

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        catalog: Optional[Any] = None,
        embedder: Optional[Any] = None,
    ) -> None:
        from src.rag_builder.catalog import default_catalog
        from src.rag_builder.config import sanitize_target_id
        from src.rag_builder.embedder import default_embedder

        self.config = config or default_config
        self.catalog = catalog or default_catalog
        self.embedder = embedder or default_embedder
        self._retrievers: Dict[str, HybridRetriever] = {}

    def get_target_retriever(self, target_id: str) -> Optional[HybridRetriever]:
        """Get or initialize a HybridRetriever for a specific isolated target."""
        from src.rag_builder.config import sanitize_target_id

        clean_id = sanitize_target_id(target_id)
        if clean_id in self._retrievers:
            return self._retrievers[clean_id]

        target_cfg = self.config.get_target_config(clean_id)
        if not target_cfg.target_dir.exists():
            return None

        chroma_mgr = ChromaDBManager(
            config=self.config, embedder=self.embedder, target_config=target_cfg
        )
        bm25_mgr = BM25IndexManager(config=self.config, target_config=target_cfg)
        retriever = HybridRetriever(
            config=self.config, chroma_manager=chroma_mgr, bm25_manager=bm25_mgr
        )
        self._retrievers[clean_id] = retriever
        return retriever

    def retrieve(self, query: str, target_id: str, k: int = 5) -> List[DocumentChunk]:
        """Perform targeted retrieval from a single isolated RAG target."""
        retriever = self.get_target_retriever(target_id)
        if not retriever:
            return []
        return retriever.retrieve(query, k=k)

    def retrieve_federated(
        self, query: str, target_ids: Optional[List[str]] = None, k: int = 5
    ) -> List[DocumentChunk]:
        """Perform federated cross-target search across multiple RAG targets."""
        if not target_ids:
            targets = self.catalog.list_targets()
            target_ids = [t.target_id for t in targets if t.status == "active"]

        if not target_ids:
            return []

        target_results: List[List[DocumentChunk]] = []
        for tid in target_ids:
            retriever = self.get_target_retriever(tid)
            if retriever:
                res = retriever.retrieve(query, k=k)
                if res:
                    target_results.append(res)

        if not target_results:
            return []
        if len(target_results) == 1:
            return target_results[0][:k]

        # Global Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}
        rrf_constant = 60

        for rlist in target_results:
            for rank, chk in enumerate(rlist, start=1):
                cid = chk.chunk_id
                chunk_map[cid] = chk
                score = 1.0 / (rrf_constant + rank)
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        return [chunk_map[cid] for cid in sorted_cids[:k]]

