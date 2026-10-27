"""Embedding model interface supporting BGE-M3 1024-dimensional local embeddings."""

import logging
from typing import List, Optional

from src.rag_builder.config import RAGConfig, default_config

logger = logging.getLogger(__name__)


class BGEEmbeddingManager:
    """Manager for loading and running BGE-M3 local embedding models."""

    _instance: Optional["BGEEmbeddingManager"] = None
    _embedder = None

    def __init__(self, config: RAGConfig = default_config) -> None:
        self.config = config
        self.model_name = config.embedding_model_name
        self.dimension = config.embedding_dimension
        self.device = self._detect_device()
        self._configure_threads()

    def _detect_device(self) -> str:
        """Detect available compute device (cuda or cpu)."""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _configure_threads(self) -> None:
        """Limit PyTorch CPU threads to preserve system responsiveness."""
        if self.device == "cpu":
            try:
                import torch
                threads = getattr(self.config, "cpu_threads", 12)
                torch.set_num_threads(threads)
                logger.info("Configured PyTorch CPU threads: %d (Balanced Mode)", threads)
            except Exception as e:
                logger.warning("Could not set PyTorch thread limit: %s", e)

    def get_langchain_embeddings(self):
        """Return a LangChain-compatible embedding object."""
        if self._embedder is not None:
            return self._embedder

        try:
            # 1. Prefer langchain_community HuggingFaceEmbeddings with local cache first
            from langchain_community.embeddings import HuggingFaceEmbeddings

            logger.info("Loading BGE-M3 embedding model: %s on %s...", self.model_name, self.device)
            try:
                self._embedder = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={"device": self.device, "local_files_only": True},
                    encode_kwargs={"normalize_embeddings": True},
                )
                return self._embedder
            except Exception:
                # If not cached locally yet, download from HuggingFace
                self._embedder = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={"device": self.device},
                    encode_kwargs={"normalize_embeddings": True},
                )
                return self._embedder
        except Exception as e:
            logger.warning("Could not initialize HuggingFaceEmbeddings directly (%s). Trying SentenceTransformer...", e)

        try:
            # 2. Fallback to raw sentence_transformers wrapper
            from langchain_core.embeddings import Embeddings
            from sentence_transformers import SentenceTransformer

            st_model = SentenceTransformer(self.model_name, device=self.device)

            class _STWrapper(Embeddings):
                def __init__(self, model):
                    self.model = model

                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    embs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                    return embs.tolist()

                def embed_query(self, text: str) -> List[float]:
                    emb = self.model.encode(text, normalize_embeddings=True)
                    return emb.tolist()

            self._embedder = _STWrapper(st_model)
            return self._embedder
        except Exception as e:
            logger.error("Failed to load sentence_transformers: %s", e)
            raise RuntimeError(f"Failed to load BGE-M3 model ({self.model_name}): {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text documents."""
        embedder = self.get_langchain_embeddings()
        return embedder.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """Embed a single search query."""
        embedder = self.get_langchain_embeddings()
        return embedder.embed_query(query)


# Global default embedding manager instance
default_embedder = BGEEmbeddingManager()
