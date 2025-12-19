# Pfad: /backend/app/services/chunking.py
"""
FlowAudit Text Chunking Service

Teilt Texte in konfigurierbare Chunks für das RAG-System.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


class ChunkStrategy(str, Enum):
    """Verfügbare Chunking-Strategien."""

    FIXED = "fixed"  # Feste Token-Größe
    PARAGRAPH = "paragraph"  # An Absatzgrenzen
    SEMANTIC = "semantic"  # An Satzgrenzen


@dataclass
class TextChunk:
    """Ein Text-Chunk mit Metadaten."""

    text: str
    index: int
    total_chunks: int
    start_char: int
    end_char: int
    token_count: int


@dataclass
class ChunkingConfig:
    """Konfiguration für das Chunking."""

    chunk_size_tokens: int = 700
    chunk_overlap_tokens: int = 120
    max_chunks: int = 6
    strategy: ChunkStrategy = ChunkStrategy.FIXED

    @classmethod
    def from_dict(cls, data: dict) -> "ChunkingConfig":
        """Erstellt Config aus Dictionary."""
        return cls(
            chunk_size_tokens=data.get("chunk_size_tokens", 700),
            chunk_overlap_tokens=data.get("chunk_overlap_tokens", 120),
            max_chunks=data.get("max_chunks", 6),
            strategy=ChunkStrategy(data.get("chunk_strategy", "fixed")),
        )


class TextChunker:
    """
    Text-Chunking-Service.

    Unterstützt verschiedene Strategien:
    - fixed: Feste Token-Größe mit Überlappung
    - paragraph: Splittet an Absatzgrenzen
    - semantic: Splittet an Satzgrenzen
    """

    # Approximation: 1 Token ≈ 4 Zeichen (für Deutsch/Englisch)
    CHARS_PER_TOKEN = 4

    def __init__(self, config: ChunkingConfig | None = None):
        """
        Initialisiert den Chunker.

        Args:
            config: Chunking-Konfiguration (optional, nutzt Defaults)
        """
        self.config = config or ChunkingConfig()

    def chunk_text(self, text: str) -> list[TextChunk]:
        """
        Teilt Text in Chunks auf.

        Args:
            text: Der zu teilende Text

        Returns:
            Liste von TextChunk-Objekten
        """
        if not text or not text.strip():
            return []

        # Strategie auswählen
        if self.config.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text)
        elif self.config.strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_by_sentence(text)
        else:
            chunks = self._chunk_fixed(text)

        # Auf max_chunks begrenzen
        if len(chunks) > self.config.max_chunks:
            chunks = chunks[: self.config.max_chunks]
            # Total anpassen
            for i, chunk in enumerate(chunks):
                chunks[i] = TextChunk(
                    text=chunk.text,
                    index=chunk.index,
                    total_chunks=self.config.max_chunks,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    token_count=chunk.token_count,
                )

        logger.debug(
            f"Text in {len(chunks)} Chunks aufgeteilt "
            f"(Strategie: {self.config.strategy.value})"
        )
        return chunks

    def _chunk_fixed(self, text: str) -> list[TextChunk]:
        """
        Feste Token-Größe mit Überlappung.

        Args:
            text: Der zu teilende Text

        Returns:
            Liste von TextChunk-Objekten
        """
        chunk_size_chars = self.config.chunk_size_tokens * self.CHARS_PER_TOKEN
        overlap_chars = self.config.chunk_overlap_tokens * self.CHARS_PER_TOKEN

        chunks: list[TextChunk] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size_chars, text_len)

            # Am Wortende abschneiden wenn möglich
            if end < text_len:
                # Suche letztes Leerzeichen vor end
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        index=len(chunks),
                        total_chunks=0,  # Wird später gesetzt
                        start_char=start,
                        end_char=end,
                        token_count=len(chunk_text) // self.CHARS_PER_TOKEN,
                    )
                )

            # Nächster Start mit Überlappung
            start = end - overlap_chars
            if start <= chunks[-1].start_char if chunks else 0:
                start = end  # Verhindere Endlosschleife

        # Total setzen
        total = len(chunks)
        return [
            TextChunk(
                text=c.text,
                index=c.index,
                total_chunks=total,
                start_char=c.start_char,
                end_char=c.end_char,
                token_count=c.token_count,
            )
            for c in chunks
        ]

    def _chunk_by_paragraph(self, text: str) -> list[TextChunk]:
        """
        Splittet an Absatzgrenzen (doppelte Zeilenumbrüche).

        Args:
            text: Der zu teilende Text

        Returns:
            Liste von TextChunk-Objekten
        """
        # Splitte an doppelten Zeilenumbrüchen
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return []

        chunk_size_chars = self.config.chunk_size_tokens * self.CHARS_PER_TOKEN
        chunks: list[TextChunk] = []
        current_text = ""
        current_start = 0

        for para in paragraphs:
            # Wenn aktueller Chunk + neuer Absatz zu groß wird
            if current_text and len(current_text) + len(para) + 2 > chunk_size_chars:
                # Aktuellen Chunk speichern
                chunks.append(
                    TextChunk(
                        text=current_text.strip(),
                        index=len(chunks),
                        total_chunks=0,
                        start_char=current_start,
                        end_char=current_start + len(current_text),
                        token_count=len(current_text) // self.CHARS_PER_TOKEN,
                    )
                )
                current_text = para
                current_start = text.find(para, current_start)
            else:
                if current_text:
                    current_text += "\n\n" + para
                else:
                    current_text = para
                    current_start = text.find(para)

        # Letzten Chunk speichern
        if current_text:
            chunks.append(
                TextChunk(
                    text=current_text.strip(),
                    index=len(chunks),
                    total_chunks=0,
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    token_count=len(current_text) // self.CHARS_PER_TOKEN,
                )
            )

        # Total setzen
        total = len(chunks)
        return [
            TextChunk(
                text=c.text,
                index=c.index,
                total_chunks=total,
                start_char=c.start_char,
                end_char=c.end_char,
                token_count=c.token_count,
            )
            for c in chunks
        ]

    def _chunk_by_sentence(self, text: str) -> list[TextChunk]:
        """
        Splittet an Satzgrenzen.

        Args:
            text: Der zu teilende Text

        Returns:
            Liste von TextChunk-Objekten
        """
        # Einfache Satz-Erkennung (., !, ?)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        chunk_size_chars = self.config.chunk_size_tokens * self.CHARS_PER_TOKEN
        chunks: list[TextChunk] = []
        current_text = ""
        current_start = 0

        for sentence in sentences:
            # Wenn aktueller Chunk + neuer Satz zu groß wird
            if current_text and len(current_text) + len(sentence) + 1 > chunk_size_chars:
                # Aktuellen Chunk speichern
                chunks.append(
                    TextChunk(
                        text=current_text.strip(),
                        index=len(chunks),
                        total_chunks=0,
                        start_char=current_start,
                        end_char=current_start + len(current_text),
                        token_count=len(current_text) // self.CHARS_PER_TOKEN,
                    )
                )
                current_text = sentence
                current_start = text.find(sentence, current_start)
            else:
                if current_text:
                    current_text += " " + sentence
                else:
                    current_text = sentence
                    current_start = text.find(sentence)

        # Letzten Chunk speichern
        if current_text:
            chunks.append(
                TextChunk(
                    text=current_text.strip(),
                    index=len(chunks),
                    total_chunks=0,
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    token_count=len(current_text) // self.CHARS_PER_TOKEN,
                )
            )

        # Total setzen
        total = len(chunks)
        return [
            TextChunk(
                text=c.text,
                index=c.index,
                total_chunks=total,
                start_char=c.start_char,
                end_char=c.end_char,
                token_count=c.token_count,
            )
            for c in chunks
        ]


# Singleton-Instanz für Default-Config
_default_chunker: TextChunker | None = None


def get_chunker(config: ChunkingConfig | None = None) -> TextChunker:
    """
    Gibt einen TextChunker zurück.

    Args:
        config: Optional spezifische Konfiguration

    Returns:
        TextChunker-Instanz
    """
    global _default_chunker

    if config:
        return TextChunker(config)

    if _default_chunker is None:
        _default_chunker = TextChunker()

    return _default_chunker
