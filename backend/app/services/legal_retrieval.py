# Pfad: /backend/app/services/legal_retrieval.py
"""
FlowAudit Legal Retrieval Service

Retrieval-Service mit Normenhierarchie-Gewichtung für juristische Texte.

Gewichtungsfaktoren:
- EU-Primärrecht (Level 1): 1.5
- EU-Verordnung (Level 2): 1.4
- EU-Richtlinie (Level 3): 1.3
- Delegierte VO (Level 4): 1.2
- Nationales Recht (Level 5): 1.1
- Verwaltungsvorschrift (Level 6): 1.0
- Guidance (Level 7): 0.9
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from app.config import get_settings
from app.rag.embeddings import get_embedding_model
from app.services.legal_chunker import LegalChunk, LegalChunker, NormHierarchy

logger = logging.getLogger(__name__)


# Hierarchie-Gewichte für Reranking
HIERARCHY_WEIGHTS: dict[int, float] = {
    NormHierarchy.EU_PRIMARY: 1.5,
    NormHierarchy.EU_REGULATION: 1.4,
    NormHierarchy.EU_DIRECTIVE: 1.3,
    NormHierarchy.DELEGATED_ACT: 1.2,
    NormHierarchy.NATIONAL_LAW: 1.1,
    NormHierarchy.ADMIN_REGULATION: 1.0,
    NormHierarchy.GUIDANCE: 0.9,
}


@dataclass
class LegalSearchResult:
    """Suchergebnis für juristische Texte."""

    content: str
    norm_citation: str
    article: Optional[str]
    paragraph: Optional[str]
    hierarchy_level: int
    similarity: float
    weighted_score: float
    cross_references: list[str]
    definitions_used: list[str]
    metadata: dict[str, Any]


class LegalRetrievalService:
    """
    Retrieval-Service mit Normenhierarchie-Gewichtung.

    Features:
    - Lokale Embeddings mit sentence-transformers
    - Hierarchie-basiertes Reranking
    - Förderperioden-Filter (2014-2020 vs. 2021-2027)
    - Querverweise als Metadaten
    """

    COLLECTION_NAME = "legal_norms"

    def __init__(self):
        """Initialisiert LegalRetrievalService."""
        self._embedding_model = get_embedding_model()
        self._chunker = LegalChunker()
        self._init_collection()

    def _init_collection(self):
        """Initialisiert ChromaDB Collection für juristische Texte."""
        import chromadb

        settings = get_settings()

        if settings.chroma_host:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
        else:
            self._client = chromadb.Client()

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "description": "Juristische Texte (EU-Verordnungen, Richtlinien, etc.)",
                "hnsw:space": "cosine",
            },
        )

    def add_regulation(
        self,
        text: str,
        celex: str,
        hierarchy_level: int = NormHierarchy.EU_REGULATION,
        funding_period: str = "2021-2027",
        title: Optional[str] = None,
    ) -> int:
        """
        Fügt eine Verordnung zur Vektordatenbank hinzu.

        Args:
            text: Volltext der Verordnung
            celex: CELEX-Nummer
            hierarchy_level: Hierarchie-Level
            funding_period: Förderperiode
            title: Titel der Verordnung

        Returns:
            Anzahl der hinzugefügten Chunks
        """
        # Chunking
        chunks = self._chunker.chunk_regulation(
            text=text,
            celex=celex,
            hierarchy_level=hierarchy_level,
        )

        if not chunks:
            logger.warning(f"Keine Chunks erstellt für CELEX {celex}")
            return 0

        # Embeddings erstellen und speichern
        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = f"{celex}_art{chunk.article or '0'}_abs{chunk.paragraph or '0'}_{chunk.chunk_index}"

            # Angereicherter Text für Embedding
            enriched_text = self._chunker.enrich_chunk_with_definitions(chunk)
            embedding = self._embedding_model.embed_text(enriched_text)

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk.content)
            metadatas.append(
                {
                    "celex": celex,
                    "norm_citation": chunk.norm_citation,
                    "article": chunk.article or "",
                    "paragraph": chunk.paragraph or "",
                    "subparagraph": chunk.subparagraph or "",
                    "hierarchy_level": chunk.hierarchy_level,
                    "funding_period": funding_period,
                    "cross_references": ",".join(chunk.cross_references),
                    "definitions_used": ",".join(chunk.definitions_used),
                    "title": title or "",
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                }
            )

        # Batch-Insert
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Hinzugefügt: {len(chunks)} Chunks für {celex} ({title or 'ohne Titel'})")
        return len(chunks)

    def add_national_law(
        self,
        text: str,
        law_name: str,
        hierarchy_level: int = NormHierarchy.NATIONAL_LAW,
    ) -> int:
        """
        Fügt nationales Recht zur Vektordatenbank hinzu.

        Args:
            text: Volltext des Gesetzes
            law_name: Name (z.B. "UStG", "HGB")
            hierarchy_level: Hierarchie-Level

        Returns:
            Anzahl der hinzugefügten Chunks
        """
        chunks = self._chunker.chunk_national_law(
            text=text,
            law_name=law_name,
            hierarchy_level=hierarchy_level,
        )

        if not chunks:
            logger.warning(f"Keine Chunks erstellt für {law_name}")
            return 0

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = f"{law_name}_para{chunk.paragraph or '0'}_{chunk.chunk_index}"

            enriched_text = self._chunker.enrich_chunk_with_definitions(chunk)
            embedding = self._embedding_model.embed_text(enriched_text)

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk.content)
            metadatas.append(
                {
                    "law_name": law_name,
                    "norm_citation": chunk.norm_citation,
                    "paragraph": chunk.paragraph or "",
                    "subparagraph": chunk.subparagraph or "",
                    "hierarchy_level": chunk.hierarchy_level,
                    "cross_references": ",".join(chunk.cross_references),
                    "definitions_used": ",".join(chunk.definitions_used),
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                }
            )

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Hinzugefügt: {len(chunks)} Chunks für {law_name}")
        return len(chunks)

    def search(
        self,
        query: str,
        funding_period: Optional[str] = None,
        n_results: int = 10,
        hierarchy_filter: Optional[list[int]] = None,
        rerank_by_hierarchy: bool = True,
    ) -> list[LegalSearchResult]:
        """
        Sucht relevante Rechtstexte mit Hierarchie-Reranking.

        Args:
            query: Suchanfrage
            funding_period: "2014-2020" oder "2021-2027" (optional)
            n_results: Anzahl Ergebnisse
            hierarchy_filter: Nur bestimmte Hierarchie-Level
            rerank_by_hierarchy: Hierarchie-Gewichtung aktivieren

        Returns:
            Liste von LegalSearchResult
        """
        # Query-Embedding
        query_embedding = self._embedding_model.embed_text(query)

        # Filter bauen
        where_filter = self._build_filter(funding_period, hierarchy_filter)

        # Mehr Ergebnisse holen für Reranking
        fetch_count = n_results * 3 if rerank_by_hierarchy else n_results

        # Suche
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_count,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        # Ergebnisse verarbeiten
        search_results = self._process_results(results, rerank_by_hierarchy)

        return search_results[:n_results]

    def search_by_article(
        self,
        celex: str,
        article: str,
        paragraph: Optional[str] = None,
    ) -> list[LegalSearchResult]:
        """
        Sucht spezifischen Artikel/Absatz.

        Args:
            celex: CELEX-Nummer
            article: Artikelnummer
            paragraph: Absatznummer (optional)

        Returns:
            Passende Chunks
        """
        where_filter: dict[str, Any] = {
            "$and": [
                {"celex": {"$eq": celex}},
                {"article": {"$eq": article}},
            ]
        }

        if paragraph:
            where_filter["$and"].append({"paragraph": {"$eq": paragraph}})

        results = self._collection.get(
            where=where_filter,
            include=["documents", "metadatas"],
        )

        search_results: list[LegalSearchResult] = []

        if results["documents"]:
            for doc, meta in zip(results["documents"], results["metadatas"]):
                search_results.append(
                    LegalSearchResult(
                        content=doc,
                        norm_citation=meta.get("norm_citation", ""),
                        article=meta.get("article"),
                        paragraph=meta.get("paragraph"),
                        hierarchy_level=meta.get("hierarchy_level", 6),
                        similarity=1.0,
                        weighted_score=1.0,
                        cross_references=meta.get("cross_references", "").split(","),
                        definitions_used=meta.get("definitions_used", "").split(","),
                        metadata=meta,
                    )
                )

        return search_results

    def _build_filter(
        self,
        funding_period: Optional[str],
        hierarchy_filter: Optional[list[int]],
    ) -> Optional[dict[str, Any]]:
        """Baut ChromaDB-Filter."""
        conditions: list[dict[str, Any]] = []

        if funding_period:
            conditions.append({"funding_period": {"$eq": funding_period}})

        if hierarchy_filter:
            conditions.append({"hierarchy_level": {"$in": hierarchy_filter}})

        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    def _process_results(
        self,
        raw_results: dict[str, Any],
        rerank_by_hierarchy: bool,
    ) -> list[LegalSearchResult]:
        """
        Verarbeitet Rohergebnisse und wendet Hierarchie-Reranking an.

        Args:
            raw_results: ChromaDB-Ergebnisse
            rerank_by_hierarchy: Reranking aktivieren

        Returns:
            Liste von LegalSearchResult
        """
        results: list[LegalSearchResult] = []

        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # Cosine-Distanz zu Similarity
            similarity = 1 - dist

            # Hierarchie-Gewicht
            hierarchy_level = meta.get("hierarchy_level", 6)
            weight = HIERARCHY_WEIGHTS.get(hierarchy_level, 1.0)

            # Gewichteter Score
            weighted_score = similarity * weight if rerank_by_hierarchy else similarity

            results.append(
                LegalSearchResult(
                    content=doc,
                    norm_citation=meta.get("norm_citation", ""),
                    article=meta.get("article"),
                    paragraph=meta.get("paragraph"),
                    hierarchy_level=hierarchy_level,
                    similarity=similarity,
                    weighted_score=weighted_score,
                    cross_references=meta.get("cross_references", "").split(",") if meta.get("cross_references") else [],
                    definitions_used=meta.get("definitions_used", "").split(",") if meta.get("definitions_used") else [],
                    metadata=meta,
                )
            )

        # Nach gewichtetem Score sortieren
        if rerank_by_hierarchy:
            results.sort(key=lambda x: x.weighted_score, reverse=True)

        return results

    def get_stats(self) -> dict[str, Any]:
        """Gibt Statistiken zur Collection zurück."""
        count = self._collection.count()
        return {
            "collection_name": self.COLLECTION_NAME,
            "total_chunks": count,
            "embedding_model": self._embedding_model.model_name,
            "embedding_dimensions": self._embedding_model.dimension,
        }

    def get_definitions(self) -> dict[str, str]:
        """Gibt extrahierte Definitionen zurück."""
        return self._chunker.get_definitions()


# Singleton
_legal_retrieval_service: LegalRetrievalService | None = None


def get_legal_retrieval_service() -> LegalRetrievalService:
    """
    Gibt LegalRetrievalService-Singleton zurück.

    Returns:
        LegalRetrievalService-Instanz
    """
    global _legal_retrieval_service
    if _legal_retrieval_service is None:
        _legal_retrieval_service = LegalRetrievalService()
    return _legal_retrieval_service
