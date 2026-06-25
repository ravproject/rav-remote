"""
Embedding Service — menggunakan ChromaDB built-in embedding function (ONNX, all-MiniLM-L6-v2).
Lebih ringan dari sentence-transformers karena tidak perlu PyTorch.
"""
import os
from loguru import logger

class EmbeddingService:
    def __init__(self):
        self._ef = None
        self.dimension = 384

    def load(self):
        if self._ef is not None:
            return
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self._ef = DefaultEmbeddingFunction()
        logger.info("Embedding model loaded via ChromaDB ONNX (384-d)")

    @property
    def ef(self):
        if self._ef is None:
            self.load()
        return self._ef

    def embed(self, text: str) -> list[float]:
        return self.ef([text[:2048]])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        truncated = [t[:2048] for t in texts]
        return self.ef(truncated)

    def is_loaded(self) -> bool:
        return self._ef is not None
