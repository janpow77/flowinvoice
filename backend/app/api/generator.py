# Pfad: /backend/app/api/generator.py
"""
FlowAudit Generator API (Admin)

Endpoints für PDF-Generator (Seminarbetrieb).
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.export import GeneratorJob

router = APIRouter()


@router.get("/generator/templates")
async def list_templates() -> dict[str, Any]:
    """
    Listet Generator-Templates.

    Returns:
        Liste der Templates mit Preview-URLs.
    """
    templates = [
        {
            "template_id": "T1_HANDWERK",
            "name": "Handwerker",
            "preview_url": "/api/generator/templates/T1_HANDWERK/preview",
        },
        {
            "template_id": "T2_SUPERMARKT",
            "name": "Supermarkt",
            "preview_url": "/api/generator/templates/T2_SUPERMARKT/preview",
        },
        {
            "template_id": "T3_CORPORATE",
            "name": "Konzern",
            "preview_url": "/api/generator/templates/T3_CORPORATE/preview",
        },
        {
            "template_id": "T4_FREELANCER",
            "name": "Freelancer",
            "preview_url": "/api/generator/templates/T4_FREELANCER/preview",
        },
        {
            "template_id": "T5_MINIMAL",
            "name": "Minimal",
            "preview_url": "/api/generator/templates/T5_MINIMAL/preview",
        },
    ]

    return {"data": templates}


@router.get("/generator/templates/{template_id}/preview")
async def get_template_preview(template_id: str):
    """
    Gibt Template-Preview zurück.

    Args:
        template_id: Template-ID

    Returns:
        Preview-Bild (PNG/SVG).
    """
    # TODO: Echte Preview-Bilder generieren
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template preview not yet implemented",
    )


@router.post("/generator/run", status_code=status.HTTP_202_ACCEPTED)
async def run_generator(
    project_id: str | None = None,
    ruleset_id: str = "DE_USTG",
    language: str = "de",
    count: int = 20,
    templates_enabled: list[str] | None = None,
    error_rate_total: float = 5.0,
    severity: int = 2,
    per_feature_error_rates: dict[str, float] | None = None,
    alias_noise_probability: float = 10.0,
    date_format_profiles: list[str] | None = None,
    output_dir_override: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> dict[str, Any]:
    """
    Startet Generator-Job (Admin only).

    Args:
        project_id: Optional Projekt-ID
        ruleset_id: Ruleset
        language: Sprache
        count: Anzahl zu generierender Rechnungen
        templates_enabled: Aktive Templates
        error_rate_total: Gesamt-Fehlerrate (%)
        severity: Schweregrad (1-5)
        per_feature_error_rates: Feature-spezifische Fehlerraten
        alias_noise_probability: Alias-Noise (%)
        date_format_profiles: Datumsformate
        output_dir_override: Ausgabeverzeichnis-Override

    Returns:
        Generator-Job-Info.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    templates = templates_enabled or ["T1_HANDWERK", "T3_CORPORATE"]
    date_formats = date_format_profiles or ["DD.MM.YYYY"]

    generator_job = GeneratorJob(
        project_id=project_id,
        ruleset_id=ruleset_id,
        language=language,
        count=count,
        templates_enabled=templates,
        settings={
            "error_rate_total": error_rate_total,
            "severity": severity,
            "per_feature_error_rates": per_feature_error_rates or {},
            "alias_noise_probability": alias_noise_probability,
            "date_format_profiles": date_formats,
        },
        status="PENDING",
    )

    session.add(generator_job)
    await session.flush()

    # TODO: Celery Task starten
    # run_generator_task.delay(generator_job.id)

    return {
        "generator_job_id": generator_job.id,
        "status": "RUNNING",
        "output_dir": generator_job.output_dir,
        "solutions_file": generator_job.solutions_file,
    }


@router.get("/generator/jobs/{generator_job_id}")
async def get_generator_job(
    generator_job_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt Generator-Job-Status zurück.

    Args:
        generator_job_id: Job-ID

    Returns:
        Job-Status und generierte Dateien.
    """
    result = await session.execute(
        select(GeneratorJob).where(GeneratorJob.id == generator_job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GeneratorJob {generator_job_id} not found",
        )

    return {
        "generator_job_id": job.id,
        "status": job.status,
        "generated_files": job.generated_files,
        "solutions_file": job.solutions_file,
    }


@router.get("/generator/jobs/{generator_job_id}/solutions")
async def get_generator_solutions(
    generator_job_id: str,
    session: AsyncSession = Depends(get_async_session),
    x_role: str = Header(default="user", alias="X-Role"),
) -> dict[str, Any]:
    """
    Gibt Lösungen zurück (Admin only).

    Args:
        generator_job_id: Job-ID

    Returns:
        Lösungen für generierte Rechnungen.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = await session.execute(
        select(GeneratorJob).where(GeneratorJob.id == generator_job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GeneratorJob {generator_job_id} not found",
        )

    # TODO: Lösungsdatei parsen
    return {
        "solutions_file": job.solutions_file,
        "entries": [],
    }
