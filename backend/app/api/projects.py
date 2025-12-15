# Pfad: /backend/app/api/projects.py
"""
FlowAudit Projects API

Endpoints für Vorhaben/Projekte.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.document import Document
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter()


@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Erstellt neues Projekt.

    Args:
        data: Projekt-Daten mit Begünstigtem und Details

    Returns:
        Projekt-ID und Erstellungszeitpunkt.
    """
    project = Project(
        ruleset_id_hint=data.ruleset_id_hint,
        ui_language_hint=data.ui_language_hint,
        beneficiary=data.beneficiary.model_dump(),
        project=data.project.model_dump(),
    )

    session.add(project)
    await session.flush()

    return {
        "project_id": project.id,
        "created_at": project.created_at.isoformat(),
    }


@router.get("/projects")
async def list_projects(
    q: str | None = Query(default=None, description="Suchbegriff"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Listet alle Projekte.

    Args:
        q: Optional Suchbegriff
        limit: Max. Anzahl
        offset: Offset

    Returns:
        Paginierte Liste der Projekte.
    """
    query = select(Project)

    if q:
        query = query.where(
            Project.project["project_title"].astext.ilike(f"%{q}%")
            | Project.beneficiary["name"].astext.ilike(f"%{q}%")
        )

    # Total count
    count_query = select(func.count(Project.id))
    if q:
        count_query = count_query.where(
            Project.project["project_title"].astext.ilike(f"%{q}%")
            | Project.beneficiary["name"].astext.ilike(f"%{q}%")
        )
    total = await session.scalar(count_query) or 0

    # Paginated results
    query = query.order_by(Project.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    projects = result.scalars().all()

    data = []
    for p in projects:
        # Document count
        doc_count = await session.scalar(
            select(func.count(Document.id)).where(Document.project_id == p.id)
        ) or 0

        data.append(
            ProjectListItem(
                project_id=p.id,
                project_title=p.project.get("project_title", ""),
                file_reference=p.project.get("file_reference"),
                beneficiary_name=p.beneficiary.get("name", ""),
                ruleset_id_hint=p.ruleset_id_hint,
                is_active=p.is_active,
                document_count=doc_count,
                created_at=p.created_at,
            )
        )

    return {
        "data": [item.model_dump() for item in data],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ProjectResponse:
    """
    Gibt Projekt-Details zurück.

    Args:
        project_id: Projekt-ID

    Returns:
        Vollständige Projekt-Daten.
    """
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return ProjectResponse(
        id=project.id,
        ruleset_id_hint=project.ruleset_id_hint,
        ui_language_hint=project.ui_language_hint,
        beneficiary=project.beneficiary,
        project=project.project,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> ProjectResponse:
    """
    Aktualisiert Projekt.

    Args:
        project_id: Projekt-ID
        data: Aktualisierte Daten

    Returns:
        Aktualisiertes Projekt.
    """
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if data.ruleset_id_hint is not None:
        project.ruleset_id_hint = data.ruleset_id_hint
    if data.ui_language_hint is not None:
        project.ui_language_hint = data.ui_language_hint
    if data.beneficiary is not None:
        project.beneficiary = data.beneficiary.model_dump()
    if data.project is not None:
        project.project = data.project.model_dump()

    await session.flush()

    return ProjectResponse(
        id=project.id,
        ruleset_id_hint=project.ruleset_id_hint,
        ui_language_hint=project.ui_language_hint,
        beneficiary=project.beneficiary,
        project=project.project,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/projects/{project_id}/activate")
async def activate_project(
    project_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Setzt Projekt als aktiv (Demo-Session).

    Args:
        project_id: Projekt-ID

    Returns:
        Bestätigung mit aktiver Projekt-ID.
    """
    # Alle anderen deaktivieren
    await session.execute(
        Project.__table__.update().values(is_active=False)
    )

    # Dieses aktivieren
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    project.is_active = True
    await session.flush()

    return {"active_project_id": project.id}
