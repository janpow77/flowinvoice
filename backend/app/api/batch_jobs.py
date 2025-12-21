"""
Batch-Jobs API

API-Endpunkte für Batch-Job-Verwaltung.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.batch_job import BatchJob
from app.models.enums import BatchJobStatus
from app.models.user import User
from app.schemas.batch_job import (
    BatchAnalyzeParams,
    BatchJobCreate,
    BatchJobListItem,
    BatchJobListResponse,
    BatchJobResponse,
    BatchJobUpdate,
)
from app.worker.celery_app import celery_app

router = APIRouter(prefix="/batch-jobs", tags=["batch-jobs"])


@router.get("", response_model=BatchJobListResponse)
async def list_batch_jobs(
    project_id: Optional[str] = Query(None, description="Filter nach Projekt"),
    status: Optional[str] = Query(None, description="Filter nach Status"),
    job_type: Optional[str] = Query(None, description="Filter nach Job-Typ"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listet alle Batch-Jobs auf.

    Unterstützt Filterung nach Projekt, Status und Job-Typ.
    """
    query = select(BatchJob).order_by(BatchJob.created_at.desc())

    if project_id:
        query = query.where(BatchJob.project_id == project_id)
    if status:
        query = query.where(BatchJob.status == status)
    if job_type:
        query = query.where(BatchJob.job_type == job_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get page
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return BatchJobListResponse(
        jobs=[BatchJobListItem.model_validate(job) for job in jobs],
        total=total,
    )


@router.post("", response_model=BatchJobResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_job(
    data: BatchJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Erstellt einen neuen Batch-Job.

    Job-Typen:
    - BATCH_ANALYZE: Mehrere Dokumente analysieren
    - BATCH_VALIDATE: Mehrere Dokumente validieren
    - BATCH_EXPORT: Ergebnisse exportieren
    - SOLUTION_APPLY: Lösungsdatei anwenden
    - RAG_REBUILD: RAG-Index neu aufbauen
    """
    # Validiere Job-Typ
    valid_types = [
        "BATCH_ANALYZE",
        "BATCH_VALIDATE",
        "BATCH_EXPORT",
        "SOLUTION_APPLY",
        "RAG_REBUILD",
    ]
    if data.job_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiger Job-Typ. Erlaubt: {', '.join(valid_types)}",
        )

    # Erstelle Job
    job = BatchJob(
        job_type=data.job_type,
        project_id=data.project_id,
        created_by_id=current_user.id,
        parameters=data.parameters,
        priority=data.priority,
        scheduled_at=data.scheduled_at,
        is_scheduled=data.scheduled_at is not None,
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Starte Job sofort, wenn nicht geplant
    if not job.is_scheduled:
        task = celery_app.send_task(
            f"app.worker.tasks.{_get_task_name(job.job_type)}",
            args=[job.id],
            queue=_get_queue_name(job.job_type),
        )
        job.celery_task_id = task.id
        job.status = BatchJobStatus.QUEUED.value
        await db.commit()
        await db.refresh(job)

    return BatchJobResponse.model_validate(job)


@router.get("/{job_id}", response_model=BatchJobResponse)
async def get_batch_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gibt einen Batch-Job zurück."""
    result = await db.execute(select(BatchJob).where(BatchJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Batch-Job nicht gefunden")

    return BatchJobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_batch_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bricht einen Batch-Job ab.

    Nur Jobs im Status PENDING, QUEUED oder RUNNING können abgebrochen werden.
    """
    result = await db.execute(select(BatchJob).where(BatchJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Batch-Job nicht gefunden")

    if job.status not in [
        BatchJobStatus.PENDING.value,
        BatchJobStatus.QUEUED.value,
        BatchJobStatus.RUNNING.value,
    ]:
        raise HTTPException(
            status_code=400,
            detail="Job kann nicht abgebrochen werden (bereits abgeschlossen)",
        )

    # Celery Task abbrechen
    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.mark_cancelled()
    await db.commit()


@router.post("/{job_id}/retry", response_model=BatchJobResponse)
async def retry_batch_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Startet einen fehlgeschlagenen Job erneut.

    Nur Jobs im Status FAILED können erneut gestartet werden.
    """
    result = await db.execute(select(BatchJob).where(BatchJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Batch-Job nicht gefunden")

    if job.status != BatchJobStatus.FAILED.value:
        raise HTTPException(
            status_code=400,
            detail="Nur fehlgeschlagene Jobs können erneut gestartet werden",
        )

    if job.retry_count >= job.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Maximale Wiederholungen ({job.max_retries}) erreicht",
        )

    # Reset und neu starten
    job.status = BatchJobStatus.PENDING.value
    job.retry_count += 1
    job.processed_items = 0
    job.successful_items = 0
    job.failed_items = 0
    job.skipped_items = 0
    job.progress_percent = 0.0
    job.errors = []
    job.warnings = []
    job.started_at = None
    job.completed_at = None

    task = celery_app.send_task(
        f"app.worker.tasks.{_get_task_name(job.job_type)}",
        args=[job.id],
        queue=_get_queue_name(job.job_type),
    )
    job.celery_task_id = task.id
    job.status = BatchJobStatus.QUEUED.value

    await db.commit()
    await db.refresh(job)

    return BatchJobResponse.model_validate(job)


# Convenience-Endpoints für häufige Job-Typen

@router.post("/analyze", response_model=BatchJobResponse)
async def create_batch_analyze_job(
    project_id: str,
    params: BatchAnalyzeParams,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Erstellt einen Batch-Analyse-Job für ein Projekt.

    Analysiert alle Dokumente im Status VALIDATED oder nur spezifische Dokumente.
    """
    job = BatchJob(
        job_type="BATCH_ANALYZE",
        project_id=project_id,
        created_by_id=current_user.id,
        parameters=params.model_dump(),
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Starte Job
    task = celery_app.send_task(
        "app.worker.tasks.batch_analyze_task",
        args=[job.id],
        queue="llm",
    )
    job.celery_task_id = task.id
    job.status = BatchJobStatus.QUEUED.value
    await db.commit()
    await db.refresh(job)

    return BatchJobResponse.model_validate(job)


# Hilfsfunktionen

def _get_task_name(job_type: str) -> str:
    """Gibt den Celery-Task-Namen für einen Job-Typ zurück."""
    task_map = {
        "BATCH_ANALYZE": "batch_analyze_task",
        "BATCH_VALIDATE": "batch_validate_task",
        "BATCH_EXPORT": "batch_export_task",
        "SOLUTION_APPLY": "solution_apply_task",
        "RAG_REBUILD": "rag_rebuild_task",
    }
    return task_map.get(job_type, "batch_analyze_task")


def _get_queue_name(job_type: str) -> str:
    """Gibt die Celery-Queue für einen Job-Typ zurück."""
    queue_map = {
        "BATCH_ANALYZE": "llm",
        "BATCH_VALIDATE": "documents",
        "BATCH_EXPORT": "export",
        "SOLUTION_APPLY": "documents",
        "RAG_REBUILD": "llm",
    }
    return queue_map.get(job_type, "documents")
