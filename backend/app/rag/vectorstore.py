# Pfad: /backend/app/rag/vectorstore.py
"""
FlowAudit Vector Store

ChromaDB-basierter Vektorspeicher für Few-Shot-Learning.
"""

import logging
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.services.chunking import ChunkingConfig, TextChunker

from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Suchergebnis aus Vektordatenbank."""

    id: str
    document: str
    metadata: dict[str, Any]
    distance: float
    score: float  # Normalisierte Ähnlichkeit (0-1)


class VectorStore:
    """
    ChromaDB Vektorspeicher.

    Speichert:
    - Validierte Rechnungsbeispiele
    - Korrigierte Fehler (mit Feedback)
    - Semantische Muster
    """

    COLLECTIONS = {
        "invoices": "Validierte Rechnungsbeispiele",
        "invoice_chunks": "Text-Chunks für granulare Suche",
        "errors": "Fehlerbeispiele mit Korrekturen",
        "patterns": "Semantische Muster",
    }

    def __init__(self, persist_directory: str | None = None):
        """
        Initialisiert VectorStore.

        Args:
            persist_directory: Pfad für persistente Speicherung
        """
        settings = get_settings()
        self.chroma_host = settings.chroma_host
        self.chroma_port = settings.chroma_port
        self.persist_directory = persist_directory

        # ChromaDB Client
        if self.chroma_host:
            # HTTP-Client für externe/Docker ChromaDB
            self._client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
            )
        else:
            # Lokaler Client
            self._client = chromadb.Client(
                ChromaSettings(
                    anonymized_telemetry=False,
                    persist_directory=persist_directory,
                )
            )

        # Embedding-Funktion
        self._embedding_model = get_embedding_model()

        # Collections initialisieren
        self._collections: dict[str, Any] = {}

    def _get_collection(self, name: str) -> Any:
        """Gibt oder erstellt Collection."""
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"description": self.COLLECTIONS.get(name, "")},
            )
        return self._collections[name]

    # =========================================================================
    # Invoice Examples (für Few-Shot)
    # =========================================================================

    def add_invoice_example(
        self,
        document_id: str,
        raw_text: str,
        extracted_data: dict[str, Any],
        assessment: str,
        errors: list[dict[str, Any]] | None = None,
        ruleset_id: str = "DE_USTG",
        chunking_config: ChunkingConfig | dict | None = None,
    ):
        """
        Fügt validiertes Rechnungsbeispiel hinzu.

        Args:
            document_id: Dokument-ID
            raw_text: Roh-Text der Rechnung
            extracted_data: Extrahierte Felder
            assessment: Bewertung (ok, review_needed, rejected)
            errors: Gefundene Fehler
            ruleset_id: Ruleset
            chunking_config: Optional Chunking-Konfiguration
        """
        collection = self._get_collection("invoices")

        # Text für Embedding vorbereiten
        embed_text = self._prepare_invoice_embed_text(raw_text, extracted_data)
        embedding = self._embedding_model.embed_text(embed_text)

        # Metadata
        metadata = {
            "ruleset_id": ruleset_id,
            "assessment": assessment,
            "has_errors": bool(errors),
            "error_count": len(errors) if errors else 0,
            "net_amount": str(extracted_data.get("net_amount", "")),
            "gross_amount": str(extracted_data.get("gross_amount", "")),
        }

        collection.upsert(
            ids=[document_id],
            embeddings=[embedding],
            documents=[embed_text],
            metadatas=[metadata],
        )

        logger.info(f"Added invoice example: {document_id}")

        # Chunking hinzufügen wenn konfiguriert
        if chunking_config and raw_text:
            self._add_invoice_chunks(
                document_id=document_id,
                raw_text=raw_text,
                extracted_data=extracted_data,
                ruleset_id=ruleset_id,
                assessment=assessment,
                chunking_config=chunking_config,
            )

    def _add_invoice_chunks(
        self,
        document_id: str,
        raw_text: str,
        extracted_data: dict[str, Any],
        ruleset_id: str,
        assessment: str,
        chunking_config: ChunkingConfig | dict,
    ):
        """
        Fügt Text-Chunks für granulare Suche hinzu.

        Args:
            document_id: Dokument-ID
            raw_text: Roh-Text
            extracted_data: Extrahierte Felder
            ruleset_id: Ruleset
            assessment: Bewertung
            chunking_config: Chunking-Konfiguration
        """
        # Config normalisieren
        if isinstance(chunking_config, dict):
            config = ChunkingConfig.from_dict(chunking_config)
        else:
            config = chunking_config

        # Chunker erstellen und Text aufteilen
        chunker = TextChunker(config)
        chunks = chunker.chunk_text(raw_text)

        if not chunks:
            logger.debug(f"No chunks generated for document {document_id}")
            return

        collection = self._get_collection("invoice_chunks")

        # Chunk-IDs und Daten vorbereiten
        chunk_ids = []
        embeddings = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{document_id}_chunk_{chunk.index}"
            chunk_ids.append(chunk_id)

            # Embedding für Chunk
            embedding = self._embedding_model.embed_text(chunk.text)
            embeddings.append(embedding)
            documents.append(chunk.text)

            # Chunk-Metadaten
            metadatas.append({
                "parent_document_id": document_id,
                "chunk_index": chunk.index,
                "total_chunks": chunk.total_chunks,
                "token_count": chunk.token_count,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "ruleset_id": ruleset_id,
                "assessment": assessment,
                # Strukturierte Daten für Kontext
                "supplier": str(extracted_data.get("supplier_name_address", ""))[:100],
                "amount": str(extracted_data.get("gross_amount", "")),
            })

        # Batch-Insert
        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Added {len(chunks)} chunks for document {document_id} "
            f"(strategy: {config.strategy.value})"
        )

    def find_similar_invoices(
        self,
        raw_text: str,
        extracted_data: dict[str, Any],
        n_results: int = 5,
        ruleset_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Findet ähnliche Rechnungsbeispiele.

        Args:
            raw_text: Roh-Text der Rechnung
            extracted_data: Extrahierte Felder
            n_results: Anzahl Ergebnisse
            ruleset_id: Filter nach Ruleset

        Returns:
            Liste von SearchResult
        """
        collection = self._get_collection("invoices")

        embed_text = self._prepare_invoice_embed_text(raw_text, extracted_data)
        embedding = self._embedding_model.embed_text(embed_text)

        # Where-Filter
        where_filter = None
        if ruleset_id:
            where_filter = {"ruleset_id": ruleset_id}

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results)

    def find_similar_chunks(
        self,
        query_text: str,
        n_results: int = 10,
        ruleset_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Findet ähnliche Text-Chunks.

        Args:
            query_text: Suchtext
            n_results: Anzahl Ergebnisse
            ruleset_id: Filter nach Ruleset

        Returns:
            Liste von SearchResult mit Chunk-Metadaten
        """
        collection = self._get_collection("invoice_chunks")

        embedding = self._embedding_model.embed_text(query_text)

        # Where-Filter
        where_filter = None
        if ruleset_id:
            where_filter = {"ruleset_id": ruleset_id}

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results)

    def _prepare_invoice_embed_text(
        self,
        raw_text: str,
        extracted_data: dict[str, Any],
    ) -> str:
        """Bereitet Text für Invoice-Embedding vor."""
        parts = []

        # Strukturierte Felder
        if extracted_data.get("supply_description"):
            parts.append(f"Leistung: {extracted_data['supply_description']}")

        if extracted_data.get("supplier_name_address"):
            parts.append(f"Lieferant: {extracted_data['supplier_name_address']}")

        # Auszug aus Rohtext
        text_preview = raw_text[:2000] if raw_text else ""
        parts.append(text_preview)

        return "\n".join(parts)

    # =========================================================================
    # Error Examples (für Korrektur-Learning)
    # =========================================================================

    def add_error_example(
        self,
        error_id: str,
        error_type: str,
        feature_id: str,
        context_text: str,
        wrong_value: str,
        correct_value: str,
        reasoning: str,
        ruleset_id: str = "DE_USTG",
    ):
        """
        Fügt Fehlerbeispiel mit Korrektur hinzu.

        Args:
            error_id: Fehler-ID
            error_type: Fehlertyp (MISSING, WRONG_FORMAT, etc.)
            feature_id: Betroffenes Feature
            context_text: Kontext-Text (Rechnungsauszug)
            wrong_value: Falscher Wert
            correct_value: Korrigierter Wert
            reasoning: Begründung
            ruleset_id: Ruleset
        """
        collection = self._get_collection("errors")

        # Text für Embedding
        embed_text = f"""
Fehlertyp: {error_type}
Feature: {feature_id}
Falscher Wert: {wrong_value}
Korrektur: {correct_value}
Kontext: {context_text[:1000]}
Begründung: {reasoning}
"""
        embedding = self._embedding_model.embed_text(embed_text)

        metadata = {
            "error_type": error_type,
            "feature_id": feature_id,
            "ruleset_id": ruleset_id,
            "wrong_value": wrong_value[:200],
            "correct_value": correct_value[:200],
        }

        collection.upsert(
            ids=[error_id],
            embeddings=[embedding],
            documents=[embed_text],
            metadatas=[metadata],
        )

        logger.info(f"Added error example: {error_id}")

    def find_similar_errors(
        self,
        error_type: str,
        feature_id: str,
        context_text: str,
        n_results: int = 3,
        ruleset_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Findet ähnliche Fehlerbeispiele.

        Args:
            error_type: Fehlertyp
            feature_id: Feature-ID
            context_text: Kontext-Text
            n_results: Anzahl Ergebnisse
            ruleset_id: Optional Ruleset-ID für Filterung

        Returns:
            Liste von SearchResult
        """
        collection = self._get_collection("errors")

        embed_text = f"""
Fehlertyp: {error_type}
Feature: {feature_id}
Kontext: {context_text[:1000]}
"""
        embedding = self._embedding_model.embed_text(embed_text)

        # Filter nach Feature und optional nach Ruleset
        where_filter: dict[str, str] = {"feature_id": feature_id}
        if ruleset_id:
            where_filter = {"$and": [{"feature_id": feature_id}, {"ruleset_id": ruleset_id}]}

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results)

    # =========================================================================
    # Semantic Patterns (für Leistungsbeschreibungs-Matching)
    # =========================================================================

    def add_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        examples: list[str],
        project_type: str | None = None,
    ):
        """
        Fügt semantisches Muster hinzu.

        Args:
            pattern_id: Pattern-ID
            pattern_type: Mustertyp (supply_description, economic_red_flag)
            description: Beschreibung des Musters
            examples: Beispieltexte
            project_type: Projekttyp (optional)
        """
        collection = self._get_collection("patterns")

        # Text für Embedding
        embed_text = f"""
Typ: {pattern_type}
Beschreibung: {description}
Beispiele: {' | '.join(examples[:5])}
"""
        embedding = self._embedding_model.embed_text(embed_text)

        metadata = {
            "pattern_type": pattern_type,
            "description": description,
            "example_count": len(examples),
        }
        if project_type:
            metadata["project_type"] = project_type

        collection.upsert(
            ids=[pattern_id],
            embeddings=[embedding],
            documents=[embed_text],
            metadatas=[metadata],
        )

        logger.info(f"Added pattern: {pattern_id}")

    def find_matching_patterns(
        self,
        text: str,
        pattern_type: str | None = None,
        n_results: int = 5,
    ) -> list[SearchResult]:
        """
        Findet passende Muster für Text.

        Args:
            text: Zu prüfender Text
            pattern_type: Filter nach Mustertyp
            n_results: Anzahl Ergebnisse

        Returns:
            Liste von SearchResult
        """
        collection = self._get_collection("patterns")

        embedding = self._embedding_model.embed_text(text)

        where_filter = None
        if pattern_type:
            where_filter = {"pattern_type": pattern_type}

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results)

    # =========================================================================
    # Utility
    # =========================================================================

    def _parse_results(self, results: dict[str, Any]) -> list[SearchResult]:
        """Parst ChromaDB-Ergebnisse zu SearchResult-Liste."""
        parsed: list[SearchResult] = []

        if not results or not results.get("ids"):
            return parsed

        ids = results["ids"][0] if results["ids"] else []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else 1.0
            # ChromaDB L2-Distanz zu Ähnlichkeit (0-1) konvertieren
            score = max(0.0, 1.0 - (distance / 2.0))

            parsed.append(SearchResult(
                id=doc_id,
                document=documents[i] if i < len(documents) else "",
                metadata=metadatas[i] if i < len(metadatas) else {},
                distance=distance,
                score=score,
            ))

        return parsed

    def get_collection_stats(self) -> dict[str, int]:
        """Gibt Statistiken für alle Collections zurück."""
        stats = {}
        for name in self.COLLECTIONS:
            try:
                collection = self._get_collection(name)
                stats[name] = collection.count()
            except Exception:
                stats[name] = 0
        return stats

    def delete_invoice_example(self, document_id: str) -> bool:
        """
        Löscht ein Rechnungsbeispiel und zugehörige Chunks.

        Args:
            document_id: Dokument-ID

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        deleted = False

        # Aus invoices Collection löschen
        try:
            collection = self._get_collection("invoices")
            collection.delete(ids=[document_id])
            deleted = True
            logger.info(f"Deleted invoice example: {document_id}")
        except Exception as e:
            logger.debug(f"Could not delete from invoices: {e}")

        # Zugehörige Chunks löschen
        try:
            chunks_collection = self._get_collection("invoice_chunks")
            # Chunks haben IDs wie "{document_id}_chunk_{index}"
            # Wir müssen nach parent_document_id filtern und dann löschen
            results = chunks_collection.get(
                where={"parent_document_id": document_id},
                include=["metadatas"],
            )
            if results and results.get("ids"):
                chunk_ids = results["ids"]
                if chunk_ids:
                    chunks_collection.delete(ids=chunk_ids)
                    logger.info(f"Deleted {len(chunk_ids)} chunks for: {document_id}")
                    deleted = True
        except Exception as e:
            logger.debug(f"Could not delete chunks: {e}")

        return deleted

    def delete_error_example(self, error_id: str) -> bool:
        """
        Löscht ein Fehlerbeispiel.

        Args:
            error_id: Fehler-ID

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        try:
            collection = self._get_collection("errors")
            collection.delete(ids=[error_id])
            logger.info(f"Deleted error example: {error_id}")
            return True
        except Exception as e:
            logger.debug(f"Could not delete error example: {e}")
            return False


# Singleton
_vectorstore: VectorStore | None = None


def get_vectorstore() -> VectorStore:
    """
    Gibt VectorStore-Singleton zurück.

    Returns:
        VectorStore-Instanz
    """
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStore()
    return _vectorstore
