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
from app.models.ruleset_checker import RulesetCheckerSettings
from app.schemas.ruleset import RulesetCreate, RulesetListItem, RulesetResponse
from app.schemas.ruleset_checker import (
    RulesetCheckerSettingsResponse,
    RulesetCheckerSettingsUpdate,
    get_default_checker_settings,
)

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
                "supported_document_types": rs.supported_document_types or ["INVOICE"],
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


@router.get("/rulesets/{ruleset_id}/llm-schema")
async def get_ruleset_llm_schema(
    ruleset_id: str,
    version: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    accept_language: str = Header(default="de", alias="Accept-Language"),
) -> dict[str, Any]:
    """
    Gibt das LLM-Schema fuer ein Regelwerk zurueck.

    Zeigt, wie das Regelwerk und die Merkmale an das LLM gesendet werden:
    - System-Prompt mit Merkmalen
    - Erwartetes Response-JSON-Schema
    - Beispiel User-Prompt-Struktur

    Args:
        ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)
        version: Optional: spezifische Version

    Returns:
        LLM-Schema mit Prompts und Response-Format.
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

    # Merkmale formatieren wie im LLM-Adapter
    is_german = accept_language.startswith("de")
    features_formatted = []
    features_json_schema = {}

    for feature in ruleset.features or []:
        feature_id = feature.get("feature_id", "")
        name = feature.get("name_de" if is_german else "name_en", feature_id)
        required_level = feature.get("required_level", "OPTIONAL")
        legal_basis = feature.get("legal_basis", "")
        category = feature.get("category", "")
        extraction_type = feature.get("extraction_type", "STRING")

        # Für Prompt-Formatierung
        required_label = {
            "REQUIRED": "PFLICHT" if is_german else "REQUIRED",
            "CONDITIONAL": "BEDINGT" if is_german else "CONDITIONAL",
            "OPTIONAL": "OPTIONAL",
        }.get(required_level, "OPTIONAL")

        features_formatted.append({
            "feature_id": feature_id,
            "name": name,
            "required_level": required_label,
            "legal_basis": legal_basis,
            "category": category,
            "extraction_type": extraction_type,
            "prompt_line": f"- {name} ({feature_id}): {required_label} | {legal_basis}",
        })

        # Für JSON-Schema
        json_type = {
            "STRING": "string",
            "TEXTBLOCK": "string",
            "DATE": "string (ISO date)",
            "DATE_OR_RANGE": "string (date or date range)",
            "MONEY": "number",
            "PERCENTAGE": "number",
            "NUMBER": "number",
        }.get(extraction_type, "string")

        features_json_schema[feature_id] = {
            "type": json_type,
            "description": name,
            "required": required_level == "REQUIRED",
        }

    # System-Prompt Vorlage
    system_prompt_template = f"""Du bist ein Experte für steuerliche Rechnungsprüfung.
Deine Aufgabe ist die Prüfung von Rechnungen nach dem Regelwerk {ruleset_id}.

REGELWERK: {ruleset.title_de if is_german else ruleset.title_en}
RECHTSRAUM: {ruleset.jurisdiction}

REGELWERK-MERKMALE:
Die folgenden Merkmale müssen geprüft werden:
""" + "\n".join([f["prompt_line"] for f in features_formatted]) + """

WICHTIG:
- Antworte IMMER auf Deutsch
- Antworte im JSON-Format
- Sei präzise und verweise auf konkrete Rechtsgrundlagen
- Nutze die deutschen Merkmalsnamen aus dem Regelwerk"""

    # Response JSON-Schema
    response_schema = {
        "type": "object",
        "required": ["semantic_check", "economic_check", "beneficiary_match", "warnings", "overall_assessment", "confidence"],
        "properties": {
            "semantic_check": {
                "type": "object",
                "properties": {
                    "supply_fits_project": {"type": "string", "enum": ["yes", "partial", "unclear", "no"]},
                    "supply_description_quality": {"type": "string", "enum": ["clear", "vague", "missing"]},
                    "reasoning": {"type": "string"},
                },
            },
            "economic_check": {
                "type": "object",
                "properties": {
                    "reasonable": {"type": "string", "enum": ["yes", "questionable", "no"]},
                    "reasoning": {"type": "string"},
                },
            },
            "beneficiary_match": {
                "type": "object",
                "properties": {
                    "matches": {"type": "string", "enum": ["yes", "partial", "no"]},
                    "detected_name": {"type": "string"},
                    "reasoning": {"type": "string"},
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "message": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                },
            },
            "overall_assessment": {"type": "string", "enum": ["ok", "review_needed", "reject"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    }

    # User-Prompt Beispielstruktur
    user_prompt_structure = """--- EXTRAHIERTE DATEN ---
{feature_id}: {extrahierter_wert} (Roh: {roh_text})
...
--- ENDE EXTRAHIERTE DATEN ---

--- RECHNUNGSTEXT (Auszug) ---
{volltext_der_rechnung}
--- ENDE RECHNUNGSTEXT ---

--- PROJEKTKONTEXT ---
Projekttitel: {projekt_titel}
Projektzeitraum: {start_datum} - {end_datum}
--- ENDE PROJEKTKONTEXT ---

--- BEGÜNSTIGTENKONTEXT ---
Name: {begünstigten_name}
Adresse: {adresse}
--- ENDE BEGÜNSTIGTENKONTEXT ---"""

    return {
        "ruleset_id": ruleset.ruleset_id,
        "version": ruleset.version,
        "title": ruleset.title_de if is_german else ruleset.title_en,
        "features_count": len(features_formatted),
        "features": features_formatted,
        "llm_schema": {
            "system_prompt": system_prompt_template,
            "user_prompt_structure": user_prompt_structure,
            "response_json_schema": response_schema,
            "features_json_schema": features_json_schema,
        },
    }


# =============================================================================
# Ruleset Checker Settings Endpoints
# (Must be defined BEFORE {ruleset_id}/{version} route to avoid path conflicts)
# =============================================================================


@router.get(
    "/rulesets/{ruleset_id}/checkers",
    response_model=RulesetCheckerSettingsResponse,
)
async def get_ruleset_checker_settings(
    ruleset_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> RulesetCheckerSettingsResponse:
    """
    Gibt die Prüfmodul-Einstellungen für ein Regelwerk zurück.

    Args:
        ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)

    Returns:
        Checker-Einstellungen für das Regelwerk.
    """
    # Prüfen ob Ruleset existiert
    ruleset_result = await session.execute(
        select(Ruleset).where(Ruleset.ruleset_id == ruleset_id)
    )
    if not ruleset_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} not found",
        )

    # Checker-Einstellungen abrufen
    result = await session.execute(
        select(RulesetCheckerSettings).where(
            RulesetCheckerSettings.ruleset_id == ruleset_id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Standard-Einstellungen zurückgeben
        return get_default_checker_settings(ruleset_id)

    return RulesetCheckerSettingsResponse(
        ruleset_id=settings.ruleset_id,
        risk_checker=settings.risk_checker,
        semantic_checker=settings.semantic_checker,
        economic_checker=settings.economic_checker,
        legal_checker=settings.legal_checker,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put(
    "/rulesets/{ruleset_id}/checkers",
    response_model=RulesetCheckerSettingsResponse,
)
async def update_ruleset_checker_settings(
    ruleset_id: str,
    data: RulesetCheckerSettingsUpdate,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> RulesetCheckerSettingsResponse:
    """
    Aktualisiert die Prüfmodul-Einstellungen für ein Regelwerk.

    Args:
        ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)
        data: Neue Einstellungen

    Returns:
        Aktualisierte Checker-Einstellungen.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Prüfen ob Ruleset existiert
    ruleset_result = await session.execute(
        select(Ruleset).where(Ruleset.ruleset_id == ruleset_id)
    )
    if not ruleset_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} not found",
        )

    # Checker-Einstellungen abrufen oder erstellen
    result = await session.execute(
        select(RulesetCheckerSettings).where(
            RulesetCheckerSettings.ruleset_id == ruleset_id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Neue Einstellungen erstellen
        settings = RulesetCheckerSettings(ruleset_id=ruleset_id)
        session.add(settings)

    # Einstellungen aktualisieren (nur wenn nicht None)
    if data.risk_checker is not None:
        settings.risk_checker = data.risk_checker.model_dump()

    if data.semantic_checker is not None:
        settings.semantic_checker = data.semantic_checker.model_dump()

    if data.economic_checker is not None:
        settings.economic_checker = data.economic_checker.model_dump()

    if data.legal_checker is not None:
        settings.legal_checker = data.legal_checker.model_dump()

    await session.flush()

    return RulesetCheckerSettingsResponse(
        ruleset_id=settings.ruleset_id,
        risk_checker=settings.risk_checker,
        semantic_checker=settings.semantic_checker,
        economic_checker=settings.economic_checker,
        legal_checker=settings.legal_checker,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.delete(
    "/rulesets/{ruleset_id}/checkers",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_ruleset_checker_settings(
    ruleset_id: str,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> None:
    """
    Setzt die Prüfmodul-Einstellungen auf Standard zurück.

    Löscht die gespeicherten Einstellungen, sodass Standard-Werte verwendet werden.

    Args:
        ruleset_id: Ruleset-ID (DE_USTG, EU_VAT, UK_VAT)
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Prüfen ob Ruleset existiert
    ruleset_result = await session.execute(
        select(Ruleset).where(Ruleset.ruleset_id == ruleset_id)
    )
    if not ruleset_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} not found",
        )

    # Checker-Einstellungen löschen
    result = await session.execute(
        select(RulesetCheckerSettings).where(
            RulesetCheckerSettings.ruleset_id == ruleset_id
        )
    )
    settings = result.scalar_one_or_none()

    if settings:
        await session.delete(settings)
        await session.flush()


# =============================================================================
# Ruleset Version Update Endpoint
# =============================================================================


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