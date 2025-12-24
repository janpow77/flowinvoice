# Pfad: /backend/app/api/legal.py
"""
FlowAudit Legal API

API-Endpunkte für juristische Text-Suche und -Verwaltung.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user import User
from app.services.legal_chunker import NormHierarchy
from app.services.legal_retrieval import (
    LegalSearchResult,
    get_legal_retrieval_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legal", tags=["legal"])


# ============================================================================
# Schemas
# ============================================================================


class LegalSearchRequest(BaseModel):
    """Suchanfrage für juristische Texte."""

    query: str = Field(..., min_length=3, description="Suchanfrage")
    funding_period: Optional[str] = Field(
        None, description="Förderperiode (2014-2020 oder 2021-2027)"
    )
    n_results: int = Field(10, ge=1, le=50, description="Anzahl Ergebnisse")
    hierarchy_filter: Optional[list[int]] = Field(
        None, description="Filter nach Hierarchie-Level (1-7)"
    )
    rerank_by_hierarchy: bool = Field(
        True, description="Hierarchie-Gewichtung aktivieren"
    )


class LegalSearchResultResponse(BaseModel):
    """Suchergebnis."""

    content: str
    norm_citation: str
    article: Optional[str]
    paragraph: Optional[str]
    hierarchy_level: int
    hierarchy_name: str
    similarity: float
    weighted_score: float
    cross_references: list[str]
    definitions_used: list[str]


class LegalSearchResponse(BaseModel):
    """Such-Response."""

    query: str
    results: list[LegalSearchResultResponse]
    total_results: int


class AddRegulationRequest(BaseModel):
    """Request zum Hinzufügen einer Verordnung (JSON)."""

    text: str = Field(..., min_length=10, description="Volltext der Verordnung")
    celex: str = Field(..., description="CELEX-Nummer (z.B. 32021R1060)")
    hierarchy_level: int = Field(
        NormHierarchy.EU_REGULATION,
        ge=1,
        le=7,
        description="Hierarchie-Level (1=EU-Primärrecht, 7=Guidance)",
    )
    funding_period: str = Field("2021-2027", description="Förderperiode")
    title: Optional[str] = Field(None, description="Titel der Verordnung")


class AddNationalLawRequest(BaseModel):
    """Request zum Hinzufügen von nationalem Recht (JSON)."""

    text: str = Field(..., min_length=10, description="Volltext des Gesetzes")
    law_name: str = Field(..., description="Name des Gesetzes (z.B. UStG)")
    hierarchy_level: int = Field(
        NormHierarchy.NATIONAL_LAW,
        ge=1,
        le=7,
        description="Hierarchie-Level",
    )


class LegalStatsResponse(BaseModel):
    """Statistiken."""

    collection_name: str
    total_chunks: int
    embedding_model: str
    embedding_dimensions: int
    definitions_count: int


# ============================================================================
# Helper Functions
# ============================================================================


def _hierarchy_level_to_name(level: int) -> str:
    """Konvertiert Hierarchie-Level zu lesbarem Namen."""
    names = {
        1: "EU-Primärrecht",
        2: "EU-Verordnung",
        3: "EU-Richtlinie",
        4: "Delegierte VO",
        5: "Nationales Recht",
        6: "Verwaltungsvorschrift",
        7: "Guidance",
    }
    return names.get(level, "Unbekannt")


def _convert_result(result: LegalSearchResult) -> LegalSearchResultResponse:
    """Konvertiert internes Result zu Response."""
    return LegalSearchResultResponse(
        content=result.content,
        norm_citation=result.norm_citation,
        article=result.article,
        paragraph=result.paragraph,
        hierarchy_level=result.hierarchy_level,
        hierarchy_name=_hierarchy_level_to_name(result.hierarchy_level),
        similarity=round(result.similarity, 4),
        weighted_score=round(result.weighted_score, 4),
        cross_references=[r for r in result.cross_references if r],
        definitions_used=[d for d in result.definitions_used if d],
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/search", response_model=LegalSearchResponse)
async def search_legal_texts(
    request: LegalSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Sucht in juristischen Texten mit Hierarchie-Gewichtung.

    Die Suche berücksichtigt:
    - Semantische Ähnlichkeit
    - Normenhierarchie (EU-Verordnung > Nationales Recht > Guidance)
    - Förderperiode (optional)
    """
    service = get_legal_retrieval_service()

    results = service.search(
        query=request.query,
        funding_period=request.funding_period,
        n_results=request.n_results,
        hierarchy_filter=request.hierarchy_filter,
        rerank_by_hierarchy=request.rerank_by_hierarchy,
    )

    return LegalSearchResponse(
        query=request.query,
        results=[_convert_result(r) for r in results],
        total_results=len(results),
    )


@router.get("/search", response_model=LegalSearchResponse)
async def search_legal_texts_get(
    query: str = Query(..., min_length=3, description="Suchanfrage"),
    funding_period: Optional[str] = Query(None, description="Förderperiode"),
    n_results: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    GET-Variante der Suche für einfache Anfragen.
    """
    service = get_legal_retrieval_service()

    results = service.search(
        query=query,
        funding_period=funding_period,
        n_results=n_results,
    )

    return LegalSearchResponse(
        query=query,
        results=[_convert_result(r) for r in results],
        total_results=len(results),
    )


@router.get("/article/{celex}/{article}", response_model=LegalSearchResponse)
async def get_article(
    celex: str,
    article: str,
    paragraph: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Ruft spezifischen Artikel/Absatz ab.

    Beispiel: /api/legal/article/32021R1060/74 für Art. 74 VO 2021/1060
    """
    service = get_legal_retrieval_service()

    results = service.search_by_article(
        celex=celex,
        article=article,
        paragraph=paragraph,
    )

    query_str = f"Art. {article}"
    if paragraph:
        query_str += f" Abs. {paragraph}"
    query_str += f" CELEX {celex}"

    return LegalSearchResponse(
        query=query_str,
        results=[_convert_result(r) for r in results],
        total_results=len(results),
    )


@router.post("/regulations")
async def add_regulation(
    text: str = Form(..., description="Volltext der Verordnung"),
    celex: str = Form(..., description="CELEX-Nummer"),
    hierarchy_level: int = Form(NormHierarchy.EU_REGULATION),
    funding_period: str = Form("2021-2027"),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    Fügt eine EU-Verordnung zur Wissensdatenbank hinzu.

    Die Verordnung wird automatisch in semantische Chunks zerlegt:
    - Artikel/Absatz-Struktur wird erkannt
    - Legaldefinitionen werden extrahiert
    - Querverweise werden als Metadaten gespeichert
    """
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren können Verordnungen hinzufügen",
        )

    service = get_legal_retrieval_service()

    chunk_count = service.add_regulation(
        text=text,
        celex=celex,
        hierarchy_level=hierarchy_level,
        funding_period=funding_period,
        title=title,
    )

    return {
        "status": "success",
        "celex": celex,
        "chunks_created": chunk_count,
        "message": f"Verordnung erfolgreich indexiert ({chunk_count} Chunks)",
    }


@router.post("/regulations/json")
async def add_regulation_json(
    request: AddRegulationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Fügt eine EU-Verordnung via JSON hinzu (empfohlen für mehrzeilige Texte).

    Die Verordnung wird automatisch in semantische Chunks zerlegt:
    - Artikel/Absatz-Struktur wird erkannt
    - Legaldefinitionen werden extrahiert
    - Querverweise werden als Metadaten gespeichert
    """
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren können Verordnungen hinzufügen",
        )

    service = get_legal_retrieval_service()

    chunk_count = service.add_regulation(
        text=request.text,
        celex=request.celex,
        hierarchy_level=request.hierarchy_level,
        funding_period=request.funding_period,
        title=request.title,
    )

    return {
        "status": "success",
        "celex": request.celex,
        "chunks_created": chunk_count,
        "message": f"Verordnung erfolgreich indexiert ({chunk_count} Chunks)",
    }


@router.post("/regulations/upload")
async def upload_regulation(
    file: UploadFile = File(..., description="Text-Datei mit Verordnung"),
    celex: str = Form(..., description="CELEX-Nummer"),
    hierarchy_level: int = Form(NormHierarchy.EU_REGULATION),
    funding_period: str = Form("2021-2027"),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    Lädt eine Verordnung als Datei hoch.

    Unterstützte Formate: .txt, .md
    """
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren können Verordnungen hochladen",
        )

    # Datei lesen
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    service = get_legal_retrieval_service()

    chunk_count = service.add_regulation(
        text=text,
        celex=celex,
        hierarchy_level=hierarchy_level,
        funding_period=funding_period,
        title=title or file.filename,
    )

    return {
        "status": "success",
        "celex": celex,
        "filename": file.filename,
        "chunks_created": chunk_count,
    }


@router.post("/national-laws")
async def add_national_law(
    text: str = Form(..., description="Volltext des Gesetzes"),
    law_name: str = Form(..., description="Name des Gesetzes"),
    hierarchy_level: int = Form(NormHierarchy.NATIONAL_LAW),
    current_user: User = Depends(get_current_user),
):
    """
    Fügt nationales Recht (z.B. UStG) zur Wissensdatenbank hinzu.
    """
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren können Gesetze hinzufügen",
        )

    service = get_legal_retrieval_service()

    chunk_count = service.add_national_law(
        text=text,
        law_name=law_name,
        hierarchy_level=hierarchy_level,
    )

    return {
        "status": "success",
        "law_name": law_name,
        "chunks_created": chunk_count,
    }


@router.post("/national-laws/json")
async def add_national_law_json(
    request: AddNationalLawRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Fügt nationales Recht via JSON hinzu (empfohlen für mehrzeilige Texte).
    """
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Nur Administratoren können Gesetze hinzufügen",
        )

    service = get_legal_retrieval_service()

    chunk_count = service.add_national_law(
        text=request.text,
        law_name=request.law_name,
        hierarchy_level=request.hierarchy_level,
    )

    return {
        "status": "success",
        "law_name": request.law_name,
        "chunks_created": chunk_count,
    }


@router.get("/stats", response_model=LegalStatsResponse)
async def get_legal_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Gibt Statistiken zur Legal-Wissensdatenbank zurück.
    """
    service = get_legal_retrieval_service()
    stats = service.get_stats()
    definitions = service.get_definitions()

    return LegalStatsResponse(
        collection_name=stats["collection_name"],
        total_chunks=stats["total_chunks"],
        embedding_model=stats["embedding_model"],
        embedding_dimensions=stats["embedding_dimensions"],
        definitions_count=len(definitions),
    )


@router.get("/definitions")
async def get_definitions(
    current_user: User = Depends(get_current_user),
):
    """
    Gibt extrahierte Legaldefinitionen zurück.
    """
    service = get_legal_retrieval_service()
    definitions = service.get_definitions()

    return {
        "definitions": definitions,
        "count": len(definitions),
    }


@router.get("/hierarchy-levels")
async def get_hierarchy_levels():
    """
    Gibt verfügbare Hierarchie-Level zurück.
    """
    return {
        "levels": [
            {"level": 1, "name": "EU-Primärrecht", "weight": 1.5},
            {"level": 2, "name": "EU-Verordnung", "weight": 1.4},
            {"level": 3, "name": "EU-Richtlinie", "weight": 1.3},
            {"level": 4, "name": "Delegierte VO", "weight": 1.2},
            {"level": 5, "name": "Nationales Recht", "weight": 1.1},
            {"level": 6, "name": "Verwaltungsvorschrift", "weight": 1.0},
            {"level": 7, "name": "Guidance", "weight": 0.9},
        ]
    }
