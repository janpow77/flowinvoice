"""
Custom Criteria API

API-Endpunkte für benutzerdefinierte Prüfkriterien.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.custom_criterion import CustomCriterion
from app.models.user import User
from app.schemas.custom_criterion import (
    CustomCriterionCreate,
    CustomCriterionListResponse,
    CustomCriterionResponse,
    CustomCriterionUpdate,
    EvaluateRequest,
    EvaluateResponse,
    CriterionEvaluationResult,
    RULE_CONFIG_EXAMPLES,
)
from app.services.custom_criteria_engine import CustomCriteriaEngine

router = APIRouter(prefix="/custom-criteria", tags=["custom-criteria"])


@router.get("", response_model=CustomCriterionListResponse)
async def list_custom_criteria(
    project_id: Optional[str] = Query(None, description="Filter nach Projekt"),
    ruleset_id: Optional[str] = Query(None, description="Filter nach Regelwerk"),
    is_active: Optional[bool] = Query(None, description="Filter nach Status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listet alle benutzerdefinierten Kriterien auf.

    Unterstützt Filterung nach Projekt, Regelwerk und Status.
    """
    query = select(CustomCriterion).order_by(
        CustomCriterion.priority.desc(),
        CustomCriterion.name,
    )

    if project_id is not None:
        # Include global criteria (project_id is None) + project-specific
        query = query.where(
            (CustomCriterion.project_id == project_id) |
            (CustomCriterion.project_id.is_(None))
        )

    if ruleset_id is not None:
        query = query.where(
            (CustomCriterion.ruleset_id == ruleset_id) |
            (CustomCriterion.ruleset_id.is_(None))
        )

    if is_active is not None:
        query = query.where(CustomCriterion.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get page
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    criteria = result.scalars().all()

    return CustomCriterionListResponse(
        criteria=[CustomCriterionResponse.model_validate(c) for c in criteria],
        total=total,
    )


@router.post("", response_model=CustomCriterionResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_criterion(
    data: CustomCriterionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Erstellt ein neues benutzerdefiniertes Kriterium.

    Unterstützte Logik-Typen:
    - SIMPLE_COMPARISON: Einfacher Wertevergleich
    - FIELD_REQUIRED: Pflichtfeldprüfung
    - DATE_RANGE: Datumsbereichsprüfung
    - PATTERN_MATCH: Regex-Musterprüfung
    - FORMULA: Formelbasierte Prüfung
    - LOOKUP: Black-/Whitelist-Prüfung
    - CONDITIONAL: Bedingte Prüfung
    - AGGREGATE: Aggregat-Prüfung
    """
    # Prüfe ob error_code bereits existiert
    existing = await db.execute(
        select(CustomCriterion).where(
            CustomCriterion.error_code == data.error_code,
            CustomCriterion.project_id == data.project_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Fehlercode '{data.error_code}' existiert bereits für dieses Projekt",
        )

    criterion = CustomCriterion(
        name=data.name,
        description=data.description,
        error_code=data.error_code,
        severity=data.severity,
        logic_type=data.logic_type,
        rule_config=data.rule_config,
        error_message_template=data.error_message_template,
        priority=data.priority,
        project_id=data.project_id,
        ruleset_id=data.ruleset_id,
        created_by_id=current_user.id,
    )

    db.add(criterion)
    await db.commit()
    await db.refresh(criterion)

    return CustomCriterionResponse.model_validate(criterion)


@router.get("/examples")
async def get_rule_config_examples():
    """
    Gibt Beispiele für Regelkonfigurationen zurück.

    Hilft beim Erstellen neuer Kriterien.
    """
    return RULE_CONFIG_EXAMPLES


@router.get("/{criterion_id}", response_model=CustomCriterionResponse)
async def get_custom_criterion(
    criterion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gibt ein benutzerdefiniertes Kriterium zurück."""
    result = await db.execute(
        select(CustomCriterion).where(CustomCriterion.id == criterion_id)
    )
    criterion = result.scalar_one_or_none()

    if not criterion:
        raise HTTPException(status_code=404, detail="Kriterium nicht gefunden")

    return CustomCriterionResponse.model_validate(criterion)


@router.put("/{criterion_id}", response_model=CustomCriterionResponse)
async def update_custom_criterion(
    criterion_id: str,
    data: CustomCriterionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aktualisiert ein benutzerdefiniertes Kriterium."""
    result = await db.execute(
        select(CustomCriterion).where(CustomCriterion.id == criterion_id)
    )
    criterion = result.scalar_one_or_none()

    if not criterion:
        raise HTTPException(status_code=404, detail="Kriterium nicht gefunden")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(criterion, field, value)

    await db.commit()
    await db.refresh(criterion)

    return CustomCriterionResponse.model_validate(criterion)


@router.delete("/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_criterion(
    criterion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Löscht ein benutzerdefiniertes Kriterium."""
    result = await db.execute(
        select(CustomCriterion).where(CustomCriterion.id == criterion_id)
    )
    criterion = result.scalar_one_or_none()

    if not criterion:
        raise HTTPException(status_code=404, detail="Kriterium nicht gefunden")

    await db.delete(criterion)
    await db.commit()


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_criteria(
    data: EvaluateRequest,
    project_id: Optional[str] = Query(None, description="Projekt-ID für kontextspezifische Kriterien"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluiert Dokumentdaten gegen alle oder ausgewählte Kriterien.

    Gibt detaillierte Ergebnisse für jedes geprüfte Kriterium zurück.
    """
    # Lade Kriterien
    query = select(CustomCriterion).where(CustomCriterion.is_active == True)

    if data.criterion_ids:
        query = query.where(CustomCriterion.id.in_(data.criterion_ids))
    elif project_id:
        query = query.where(
            (CustomCriterion.project_id == project_id) |
            (CustomCriterion.project_id.is_(None))
        )

    result = await db.execute(query)
    criteria = result.scalars().all()

    if not criteria:
        return EvaluateResponse(
            passed=True,
            total_checked=0,
            passed_count=0,
            failed_count=0,
            results=[],
        )

    # Projektkontext laden falls vorhanden
    project_context = {}
    if project_id:
        from app.models.project import Project
        proj_result = await db.execute(select(Project).where(Project.id == project_id))
        project = proj_result.scalar_one_or_none()
        if project and project.project_period:
            project_context = {
                "start_date": project.project_period.get("start"),
                "end_date": project.project_period.get("end"),
            }

    # Evaluiere
    engine = CustomCriteriaEngine(project_context=project_context)
    results = engine.evaluate_all(list(criteria), data.document_data)

    # Zähle Ergebnisse
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    return EvaluateResponse(
        passed=failed_count == 0,
        total_checked=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=[
            CriterionEvaluationResult(
                criterion_id=r.criterion_id,
                criterion_name=r.criterion_name,
                error_code=r.error_code,
                passed=r.passed,
                severity=r.severity,
                message=r.message,
                field=r.field,
                expected=r.expected,
                actual=r.actual,
            )
            for r in results
        ],
    )


@router.post("/{criterion_id}/toggle", response_model=CustomCriterionResponse)
async def toggle_criterion(
    criterion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aktiviert/Deaktiviert ein Kriterium."""
    result = await db.execute(
        select(CustomCriterion).where(CustomCriterion.id == criterion_id)
    )
    criterion = result.scalar_one_or_none()

    if not criterion:
        raise HTTPException(status_code=404, detail="Kriterium nicht gefunden")

    criterion.is_active = not criterion.is_active
    await db.commit()
    await db.refresh(criterion)

    return CustomCriterionResponse.model_validate(criterion)
