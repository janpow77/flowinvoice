# Pfad: /backend/app/api/rulesets.py
"""
FlowAudit Rulesets API

Endpoints für Regelwerke (DE_USTG, EU_VAT, UK_VAT).
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.ruleset import Ruleset
from app.schemas.ruleset import RulesetCreate, RulesetListItem, RulesetResponse

router = APIRouter()


@router.get("/rulesets", response_model=dict[str, list[RulesetListItem]])
async def list_rulesets(
    session: AsyncSession = Depends(get_async_session),
    accept_language: str = Header(default="de", alias="Accept-Language"),
) -> dict[str, Any]:
    """
    Listet alle verfügbaren Rulesets.

    Returns:
        Liste der Rulesets mit Basisinfos.
    """
    result = await session.execute(select(Ruleset).order_by(Ruleset.ruleset_id))
    rulesets = result.scalars().all()

    data = []
    for rs in rulesets:
        title = rs.title_de if accept_language.startswith("de") else rs.title_en
        data.append(
            {
                "ruleset_id": rs.ruleset_id,
                "version": rs.version,
                "title": title,
                "language_support": rs.supported_ui_languages,
            }
        )

    return {"data": data}


@router.get("/rulesets/{ruleset_id}", response_model=RulesetResponse)
async def get_ruleset(
    ruleset_id: str,
    version: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> RulesetResponse:
    """
    Gibt vollständiges Ruleset zurück.

    Args:
        ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)
        version: Optional: spezifische Version

    Returns:
        Vollständiges Ruleset mit Features.
    """
    query = select(Ruleset).where(Ruleset.ruleset_id == ruleset_id)

    if version:
        query = query.where(Ruleset.version == version)
    else:
        query = query.order_by(Ruleset.version.desc())

    result = await session.execute(query)
    ruleset = result.scalar_one_or_none()

    if not ruleset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} not found",
        )

    return RulesetResponse(
        ruleset_id=ruleset.ruleset_id,
        version=ruleset.version,
        jurisdiction=ruleset.jurisdiction,
        title_de=ruleset.title_de,
        title_en=ruleset.title_en,
        legal_references=ruleset.legal_references,
        default_language=ruleset.default_language,
        supported_ui_languages=ruleset.supported_ui_languages,
        currency_default=ruleset.currency_default,
        features=ruleset.features,
        special_rules=ruleset.special_rules,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
    )


@router.post("/rulesets", status_code=status.HTTP_201_CREATED)
async def create_ruleset(
    data: RulesetCreate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> dict[str, str]:
    """
    Erstellt neues Ruleset (Admin only).

    Args:
        data: Ruleset-Daten

    Returns:
        Erstelltes Ruleset mit ID und Version.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Prüfen ob bereits existiert
    existing = await session.execute(
        select(Ruleset).where(
            Ruleset.ruleset_id == data.ruleset_id,
            Ruleset.version == data.version,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ruleset {data.ruleset_id} v{data.version} already exists",
        )

    ruleset = Ruleset(
        ruleset_id=data.ruleset_id,
        version=data.version,
        jurisdiction=data.jurisdiction,
        title_de=data.title_de,
        title_en=data.title_en,
        legal_references=data.legal_references,
        features=data.features,
        default_language=data.default_language,
        supported_ui_languages=data.supported_ui_languages,
        currency_default=data.currency_default,
        special_rules=data.special_rules,
    )

    session.add(ruleset)
    await session.flush()

    return {"ruleset_id": ruleset.ruleset_id, "version": ruleset.version}


@router.put("/rulesets/{ruleset_id}/{version}")
async def update_ruleset(
    ruleset_id: str,
    version: str,
    data: RulesetCreate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetResponse:
    """
    Aktualisiert Ruleset (Admin only).

    Hinweis: Rulesets sollten immutable sein.
    Besser: neue Version erstellen.

    Args:
        ruleset_id: Ruleset-ID
        version: Version
        data: Aktualisierte Daten

    Returns:
        Aktualisiertes Ruleset.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(Ruleset).where(
            Ruleset.ruleset_id == ruleset_id,
            Ruleset.version == version,
        )
    )
    ruleset = result.scalar_one_or_none()

    if not ruleset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} v{version} not found",
        )

    # Update fields
    ruleset.title_de = data.title_de
    ruleset.title_en = data.title_en
    ruleset.legal_references = data.legal_references
    ruleset.features = data.features
    ruleset.special_rules = data.special_rules

    await session.flush()

    return RulesetResponse(
        ruleset_id=ruleset.ruleset_id,
        version=ruleset.version,
        jurisdiction=ruleset.jurisdiction,
        title_de=ruleset.title_de,
        title_en=ruleset.title_en,
        legal_references=ruleset.legal_references,
        default_language=ruleset.default_language,
        supported_ui_languages=ruleset.supported_ui_languages,
        currency_default=ruleset.currency_default,
        features=ruleset.features,
        special_rules=ruleset.special_rules,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
    )
