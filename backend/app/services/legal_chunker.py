# Pfad: /backend/app/services/legal_chunker.py
"""
FlowAudit Legal Chunker

Chunking-Strategie für juristische Texte (EU-Verordnungen, Richtlinien, etc.).

Besonderheiten:
1. Artikel/Absatz als natürliche Chunk-Grenze
2. Definitionen separat indexieren und verknüpfen
3. Querverweise auflösen und als Metadaten speichern
4. Hierarchie-Level für Gewichtung
"""

import logging
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

logger = logging.getLogger(__name__)


class NormHierarchy(IntEnum):
    """Normenhierarchie für Gewichtung bei Retrieval."""

    EU_PRIMARY = 1  # EU-Primärrecht (Verträge)
    EU_REGULATION = 2  # EU-Verordnung (direkt anwendbar)
    EU_DIRECTIVE = 3  # EU-Richtlinie (umzusetzen)
    DELEGATED_ACT = 4  # Delegierte Verordnung
    NATIONAL_LAW = 5  # Nationales Recht (UStG, HGB, etc.)
    ADMIN_REGULATION = 6  # Verwaltungsvorschrift
    GUIDANCE = 7  # Guidance, Leitlinien, EGESIF


@dataclass
class LegalChunk:
    """Ein semantisch zusammenhängender Rechtstext-Abschnitt."""

    content: str
    article: Optional[str] = None
    paragraph: Optional[str] = None
    subparagraph: Optional[str] = None
    letter: Optional[str] = None
    norm_citation: str = ""  # z.B. "Art. 74 Abs. 1 VO 2021/1060"
    hierarchy_level: int = NormHierarchy.ADMIN_REGULATION
    cross_references: list[str] = field(default_factory=list)
    definitions_used: list[str] = field(default_factory=list)
    celex: str = ""  # CELEX-Nummer
    chunk_index: int = 0
    total_chunks: int = 0


class LegalChunker:
    """
    Chunking-Strategie für juristische Texte.

    Prinzipien:
    1. Artikel/Paragraph als natürliche Chunk-Grenze
    2. Definitionen separat indexieren und verknüpfen
    3. Querverweise auflösen und als Metadaten speichern
    4. Hierarchie-Level für Gewichtung
    """

    # Muster für Artikelgliederung
    ARTICLE_PATTERN = re.compile(
        r"(?:Artikel|Art\.?)\s+(\d+[a-z]?)", re.IGNORECASE
    )
    PARAGRAPH_PATTERN = re.compile(
        r"\((\d+)\)|Absatz\s+(\d+)|Abs\.\s*(\d+)", re.IGNORECASE
    )
    SUBPARAGRAPH_PATTERN = re.compile(
        r"(?:Unterabsatz|UAbs\.?)\s+(\d+)", re.IGNORECASE
    )
    LETTER_PATTERN = re.compile(r"(?:Buchstabe|lit\.?)\s+([a-z])", re.IGNORECASE)

    # Querverweise erkennen
    CROSS_REF_PATTERNS = [
        re.compile(
            r"(?:gemäß|nach|im Sinne (?:des|der)|"
            r"nach Maßgabe (?:des|der)|"
            r"unbeschadet (?:des|der)|"
            r"vorbehaltlich (?:des|der))\s+"
            r"(?:Artikel|Art\.?)\s+(\d+[a-z]?)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:Artikel|Art\.?)\s+(\d+[a-z]?)\s+"
            r"(?:Absatz|Abs\.?)\s+(\d+)",
            re.IGNORECASE,
        ),
        re.compile(r"§\s*(\d+[a-z]?)\s*(?:Abs\.?\s*(\d+))?", re.IGNORECASE),
    ]

    # Unicode Anführungszeichen für deutsche/europäische Texte
    # „ = U+201E (German opening), " = U+201C (German closing), " = U+201D (English closing)
    # « » = French quotes, ' ' = single quotes
    QUOTE_OPEN = r'[„"\'«\u201E\u201C\u00AB]'
    QUOTE_CLOSE = r'["\'"»\u201C\u201D\u00BB]'

    # Definitionen erkennen (typischerweise Art. 2)
    DEFINITION_PATTERNS = [
        # "1. „Begriff" den/die/eine Definition..." (EU-Verordnungen)
        re.compile(
            r'(\d+)\.\s*[„"\'«\u201E\u201C\u00AB]([\w\-\s]+)["\'"»\u201C\u201D\u00BB]\s+'
            r'(.+?)(?=\n\s*\d+\.\s*[„"\'«\u201E\u201C\u00AB]|\n\n|\Z)',
            re.DOTALL,
        ),
        # "1. 'Begriff' bezeichnet/bedeutet..." (mit Verb)
        re.compile(
            r'(\d+)\.\s*[„"\'«\u201E\u201C\u00AB]([\w\-\s]+)["\'"»\u201C\u201D\u00BB]\s+'
            r"(?:bezeichnet|bedeutet|ist|sind|meint)\s+(.+?)(?=\d+\.\s*[„\"\'«\u201E\u201C\u00AB]|\n\n|\Z)",
            re.DOTALL,
        ),
        # "(a) 'Begriff' bedeutet..." (Buchstaben-Nummerierung)
        re.compile(
            r'\(([a-z])\)\s*[„"\'«\u201E\u201C\u00AB]([\w\-\s]+)["\'"»\u201C\u201D\u00BB]\s+'
            r'(.+?)(?=\([a-z]\)\s*[„"\'«\u201E\u201C\u00AB]|\n\n|\Z)',
            re.DOTALL,
        ),
    ]

    def __init__(self, max_chunk_size: int = 1500):
        """
        Initialisiert LegalChunker.

        Args:
            max_chunk_size: Maximale Chunk-Größe in Zeichen
        """
        self.max_chunk_size = max_chunk_size
        self.definitions_cache: dict[str, str] = {}

    def chunk_regulation(
        self,
        text: str,
        celex: str,
        hierarchy_level: int = NormHierarchy.EU_REGULATION,
    ) -> list[LegalChunk]:
        """
        Zerlegt eine Verordnung in semantische Chunks.

        Args:
            text: Volltext der Verordnung
            celex: CELEX-Nummer (z.B. 32021R1060)
            hierarchy_level: 1-7 nach Normenhierarchie

        Returns:
            Liste von LegalChunk-Objekten
        """
        chunks: list[LegalChunk] = []

        # Zuerst Definitionen extrahieren (meist Art. 2)
        definitions = self._extract_definitions(text)
        self.definitions_cache.update(definitions)
        logger.info(f"Extrahierte {len(definitions)} Legaldefinitionen")

        # Artikel identifizieren
        articles = self._split_into_articles(text)
        logger.info(f"Gefunden: {len(articles)} Artikel")

        for article_num, article_text in articles.items():
            # Absätze innerhalb des Artikels
            paragraphs = self._split_into_paragraphs(article_text)

            for para_num, para_text in paragraphs.items():
                # Prüfen ob Chunk zu groß
                if len(para_text) > self.max_chunk_size:
                    # Unterabsätze oder Sätze als Grenze
                    sub_chunks = self._split_large_paragraph(para_text)
                    for i, sub_text in enumerate(sub_chunks):
                        chunks.append(
                            self._create_chunk(
                                content=sub_text,
                                article=article_num,
                                paragraph=para_num,
                                subparagraph=str(i + 1) if len(sub_chunks) > 1 else None,
                                celex=celex,
                                hierarchy_level=hierarchy_level,
                            )
                        )
                else:
                    chunks.append(
                        self._create_chunk(
                            content=para_text,
                            article=article_num,
                            paragraph=para_num,
                            subparagraph=None,
                            celex=celex,
                            hierarchy_level=hierarchy_level,
                        )
                    )

        # Chunk-Indices setzen
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = total

        logger.info(f"Verordnung in {total} Chunks aufgeteilt (CELEX: {celex})")
        return chunks

    def chunk_national_law(
        self,
        text: str,
        law_name: str,
        hierarchy_level: int = NormHierarchy.NATIONAL_LAW,
    ) -> list[LegalChunk]:
        """
        Zerlegt nationales Recht (z.B. UStG) in Chunks.

        Args:
            text: Volltext des Gesetzes
            law_name: Name des Gesetzes (z.B. "UStG", "HGB")
            hierarchy_level: Hierarchie-Level

        Returns:
            Liste von LegalChunk-Objekten
        """
        chunks: list[LegalChunk] = []

        # Paragraphen identifizieren (§ X)
        paragraphs = self._split_into_paragraphs_national(text)
        logger.info(f"Gefunden: {len(paragraphs)} Paragraphen in {law_name}")

        for para_num, para_text in paragraphs.items():
            if len(para_text) > self.max_chunk_size:
                sub_chunks = self._split_large_paragraph(para_text)
                for i, sub_text in enumerate(sub_chunks):
                    chunk = self._create_chunk(
                        content=sub_text,
                        article=None,
                        paragraph=para_num,
                        subparagraph=str(i + 1) if len(sub_chunks) > 1 else None,
                        celex="",
                        hierarchy_level=hierarchy_level,
                    )
                    chunk.norm_citation = f"§ {para_num} {law_name}"
                    if len(sub_chunks) > 1:
                        chunk.norm_citation += f" (Teil {i + 1})"
                    chunks.append(chunk)
            else:
                chunk = self._create_chunk(
                    content=para_text,
                    article=None,
                    paragraph=para_num,
                    subparagraph=None,
                    celex="",
                    hierarchy_level=hierarchy_level,
                )
                chunk.norm_citation = f"§ {para_num} {law_name}"
                chunks.append(chunk)

        # Chunk-Indices setzen
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = total

        return chunks

    def _extract_definitions(self, text: str) -> dict[str, str]:
        """
        Extrahiert Legaldefinitionen (typischerweise Art. 2).

        Args:
            text: Volltext

        Returns:
            Dict: {"Unregelmäßigkeit": "Definition..."}
        """
        definitions: dict[str, str] = {}

        for pattern in self.DEFINITION_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 3:
                    # Pattern mit Nummer: (nummer, term, definition)
                    term = groups[1].strip()
                    definition = groups[2].strip()
                elif len(groups) >= 2:
                    # Pattern ohne Nummer: (term, definition)
                    term = groups[0].strip()
                    definition = groups[1].strip()
                else:
                    continue

                # Definition auf 500 Zeichen begrenzen
                if len(definition) > 500:
                    definition = definition[:500] + "..."

                definitions[term] = definition

        return definitions

    def _split_into_articles(self, text: str) -> dict[str, str]:
        """
        Teilt Text in Artikel auf.

        Args:
            text: Volltext

        Returns:
            Dict: {"1": "Artikel 1 Text...", "2": "Artikel 2 Text..."}
        """
        articles: dict[str, str] = {}

        # Artikel-Grenzen finden
        matches = list(self.ARTICLE_PATTERN.finditer(text))

        if not matches:
            # Keine Artikel gefunden -> gesamten Text als einen Artikel
            articles["1"] = text.strip()
            return articles

        for i, match in enumerate(matches):
            article_num = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            articles[article_num] = text[start:end].strip()

        return articles

    def _split_into_paragraphs(self, article_text: str) -> dict[str, str]:
        """
        Teilt Artikel in Absätze auf.

        Args:
            article_text: Artikeltext

        Returns:
            Dict: {"1": "Absatz 1...", "2": "Absatz 2..."}
        """
        paragraphs: dict[str, str] = {}

        # Nach (1), (2), ... oder Abs. 1, Abs. 2, ... suchen
        matches = list(self.PARAGRAPH_PATTERN.finditer(article_text))

        if not matches:
            # Keine Absatznummerierung -> gesamter Artikel ist ein Chunk
            paragraphs["1"] = article_text
            return paragraphs

        for i, match in enumerate(matches):
            para_num = match.group(1) or match.group(2) or match.group(3)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(article_text)
            paragraphs[para_num] = article_text[start:end].strip()

        return paragraphs

    def _split_into_paragraphs_national(self, text: str) -> dict[str, str]:
        """
        Teilt nationales Recht in Paragraphen (§) auf.

        Args:
            text: Gesetzestext

        Returns:
            Dict: {"14": "§ 14 Text...", "15": "§ 15 Text..."}
        """
        paragraphs: dict[str, str] = {}

        # § X Muster
        para_pattern = re.compile(r"§\s*(\d+[a-z]?)", re.IGNORECASE)
        matches = list(para_pattern.finditer(text))

        if not matches:
            paragraphs["1"] = text.strip()
            return paragraphs

        for i, match in enumerate(matches):
            para_num = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            paragraphs[para_num] = text[start:end].strip()

        return paragraphs

    def _split_large_paragraph(self, text: str) -> list[str]:
        """
        Teilt zu große Absätze an Unterabsätzen oder Satzgrenzen.

        Args:
            text: Absatztext

        Returns:
            Liste von Teil-Chunks
        """
        # Erst nach Unterabsätzen versuchen (a), b), 1., 2., etc.)
        subparas = re.split(r"\n\s*(?=[a-z]\)|\d+\.)", text)
        if len(subparas) > 1:
            result = [s.strip() for s in subparas if s.strip()]
            if result:
                return result

        # Sonst an Satzgrenzen
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) > self.max_chunk_size:
                if current:
                    chunks.append(current.strip())
                current = sentence
            else:
                current += " " + sentence if current else sentence

        if current:
            chunks.append(current.strip())

        return chunks if chunks else [text]

    def _create_chunk(
        self,
        content: str,
        article: Optional[str],
        paragraph: Optional[str],
        subparagraph: Optional[str],
        celex: str,
        hierarchy_level: int,
    ) -> LegalChunk:
        """
        Erstellt LegalChunk mit Metadaten.

        Args:
            content: Chunk-Inhalt
            article: Artikelnummer
            paragraph: Absatznummer
            subparagraph: Unterabsatznummer
            celex: CELEX-Nummer
            hierarchy_level: Hierarchie-Level

        Returns:
            LegalChunk-Objekt
        """
        # Normzitat bauen
        citation_parts = []
        if article:
            citation_parts.append(f"Art. {article}")
        if paragraph:
            citation_parts.append(f"Abs. {paragraph}")
        if subparagraph:
            citation_parts.append(f"UAbs. {subparagraph}")

        # CELEX zu lesbarem Namen
        norm_name = self._celex_to_citation(celex) if celex else ""
        citation = " ".join(citation_parts)
        if norm_name:
            citation += f" {norm_name}"

        # Querverweise extrahieren
        cross_refs = self._extract_cross_references(content)

        # Verwendete Definitionen erkennen
        definitions_used = [
            term
            for term in self.definitions_cache
            if term.lower() in content.lower()
        ]

        return LegalChunk(
            content=content,
            article=article,
            paragraph=paragraph,
            subparagraph=subparagraph,
            norm_citation=citation.strip(),
            hierarchy_level=hierarchy_level,
            cross_references=cross_refs,
            definitions_used=definitions_used,
            celex=celex,
        )

    def _extract_cross_references(self, text: str) -> list[str]:
        """
        Extrahiert Querverweise aus Text.

        Args:
            text: Zu durchsuchender Text

        Returns:
            Liste von Querverweisen
        """
        refs: list[str] = []

        for pattern in self.CROSS_REF_PATTERNS:
            for match in pattern.finditer(text):
                ref = match.group(0)
                if ref not in refs:
                    refs.append(ref)

        return refs

    def _celex_to_citation(self, celex: str) -> str:
        """
        Wandelt CELEX in Zitierform um.

        Args:
            celex: CELEX-Nummer (z.B. 32021R1060)

        Returns:
            Zitierform (z.B. "VO (EU) 2021/1060")
        """
        if not celex:
            return ""

        # 32021R1060 -> VO (EU) 2021/1060
        match = re.match(r"3(\d{4})([RL])(\d+)", celex)
        if match:
            year, type_code, number = match.groups()
            type_name = "VO" if type_code == "R" else "RL"
            return f"{type_name} (EU) {year}/{number}"

        return celex

    def get_definitions(self) -> dict[str, str]:
        """
        Gibt extrahierte Definitionen zurück.

        Returns:
            Dict mit Definitionen
        """
        return self.definitions_cache.copy()

    def enrich_chunk_with_definitions(
        self, chunk: LegalChunk, max_definitions: int = 3
    ) -> str:
        """
        Reichert Chunk-Text mit Definitionen an.

        Args:
            chunk: LegalChunk
            max_definitions: Maximale Anzahl Definitionen

        Returns:
            Angereicherter Text für Embedding
        """
        parts = [
            chunk.norm_citation,
            "",
            chunk.content,
        ]

        # Definitionen hinzufügen falls vorhanden
        if chunk.definitions_used:
            parts.append("")
            parts.append("Begriffsdefinitionen:")
            for term in chunk.definitions_used[:max_definitions]:
                if term in self.definitions_cache:
                    definition = self.definitions_cache[term][:200]
                    parts.append(f"- {term}: {definition}")

        return "\n".join(parts)


# Singleton
_legal_chunker: LegalChunker | None = None


def get_legal_chunker(max_chunk_size: int = 1500) -> LegalChunker:
    """
    Gibt LegalChunker-Singleton zurück.

    Args:
        max_chunk_size: Maximale Chunk-Größe

    Returns:
        LegalChunker-Instanz
    """
    global _legal_chunker
    if _legal_chunker is None:
        _legal_chunker = LegalChunker(max_chunk_size=max_chunk_size)
    return _legal_chunker
