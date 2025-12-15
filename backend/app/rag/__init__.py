# Pfad: /backend/app/rag/__init__.py
"""
FlowAudit RAG Module

RAG-Komponente mit ChromaDB für Few-Shot-Learning.
"""

from .embeddings import EmbeddingModel, get_embedding_model
from .service import (
    FewShotExample,
    RAGContext,
    RAGService,
    get_rag_service,
    init_default_patterns,
)
from .vectorstore import SearchResult, VectorStore, get_vectorstore

__all__ = [
    # Embeddings
    "EmbeddingModel",
    "get_embedding_model",
    # VectorStore
    "VectorStore",
    "get_vectorstore",
    "SearchResult",
    # Service
    "RAGService",
    "get_rag_service",
    "RAGContext",
    "FewShotExample",
    "init_default_patterns",
]
