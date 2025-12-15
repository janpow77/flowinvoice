# Pfad: /backend/app/api/export.py
"""
FlowAudit Export API

Endpoints für Daten-Export.
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.export import ExportJob
from app.worker.tasks import export_results_task

router = APIRouter()


@router.post("/projects/{project_id}/export", status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    project_id: str,
    format: str = "XLSX",
    only_status: list[str] | None = None,
    include_payloads: bool = False,
    include_llm_responses: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Erstellt Export-Job.

    Args:
        project_id: Projekt-ID
        format: XLSX, CSV, JSON
        only_status: Optional Status-Filter
        include_payloads: Payloads einschließen
        include_llm_responses: LLM-Responses einschließen

    Returns:
        Export-Job-Info.
    """
    export_job = ExportJob(
        project_id=project_id,
        format=format,
        status="PENDING",
        options={
            "only_status": only_status or ["ACCEPTED"],
            "include_payloads": include_payloads,
            "include_llm_responses": include_llm_responses,
        },
    )

    session.add(export_job)
    await session.commit()

    # Celery Task für Export starten
    task = export_results_task.delay(export_job.id)

    return {
        "export_job_id": export_job.id,
        "status": "RUNNING",
        "task_id": task.id,
    }


@router.get("/exports/{export_job_id}")
async def get_export_job(
    export_job_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt Export-Job-Status zurück.

    Args:
        export_job_id: Job-ID

    Returns:
        Job-Status und Download-URL.
    """
    result = await session.execute(select(ExportJob).where(ExportJob.id == export_job_id))
    export_job = result.scalar_one_or_none()

    if not export_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ExportJob {export_job_id} not found",
        )

    return {
        "export_job_id": export_job.id,
        "status": export_job.status,
        "file_path": export_job.file_path,
        "download_url": f"/api/exports/{export_job.id}/file" if export_job.file_path else None,
    }


@router.get("/exports/{export_job_id}/file")
async def download_export(
    export_job_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Download Export-Datei.

    Args:
        export_job_id: Job-ID

    Returns:
        Datei-Stream.
    """
    from pathlib import Path

    result = await session.execute(select(ExportJob).where(ExportJob.id == export_job_id))
    export_job = result.scalar_one_or_none()

    if not export_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ExportJob {export_job_id} not found",
        )

    if not export_job.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not ready",
        )

    file_path = Path(export_job.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found on disk",
        )

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if export_job.format == "CSV":
        media_type = "text/csv"
    elif export_job.format == "JSON":
        media_type = "application/json"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )
