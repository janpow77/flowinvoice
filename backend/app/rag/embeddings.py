# Pfad: /backend/app/rag/embeddings.py
"""
FlowAudit Embeddings

Embedding-Generierung für RAG-System.
"""

import logging

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Embedding-Modell für Vektorisierung.

    Verwendet sentence-transformers für lokale Embeddings.
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialisiert Embedding-Modell.

        Args:
            model_name: Modell-Name (default: aus Settings)
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy Loading des Modells."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """
        Erstellt Embedding für Text.

        Args:
            text: Zu vektorisierender Text

        Returns:
            Embedding-Vektor
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        result: list[float] = embedding.tolist()
        return result

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Erstellt Embeddings für mehrere Texte.

        Args:
            texts: Zu vektorisierende Texte

        Returns:
            Liste von Embedding-Vektoren
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Gibt Embedding-Dimension zurück."""
        dim: int = self.model.get_sentence_embedding_dimension()
        return dim


# Singleton
_embedding_model: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    """
    Gibt Embedding-Model-Singleton zurück.

    Returns:
        EmbeddingModel-Instanz
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
