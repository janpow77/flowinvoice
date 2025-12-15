# Pfad: /backend/app/api/generator.py
"""
FlowAudit Generator API (Admin)

Endpoints für PDF-Generator (Seminarbetrieb).
"""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.export import GeneratorJob
from app.worker.tasks import generate_invoices_task

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
        Preview als HTML.
    """
    # Template-Konfigurationen mit Vorschau-Daten
    templates_preview = {
        "T1_HANDWERK": {
            "name": "Meister Müller Handwerk GmbH",
            "address": "Werkstattstraße 15, 80331 München",
            "vat_id": "DE123456789",
            "description": "Reparaturarbeiten und Materialien",
            "style": "traditional",
        },
        "T2_SUPERMARKT": {
            "name": "Frischemarkt GmbH",
            "address": "Marktplatz 1, 10115 Berlin",
            "vat_id": "DE987654321",
            "description": "Lebensmittel und Haushaltswaren",
            "style": "receipt",
        },
        "T3_CORPORATE": {
            "name": "Enterprise Solutions AG",
            "address": "Business Tower, 60311 Frankfurt",
            "vat_id": "DE111222333",
            "description": "IT-Beratung und Softwareentwicklung",
            "style": "corporate",
        },
        "T4_FREELANCER": {
            "name": "Max Mustermann",
            "address": "Homeoffice Weg 42, 50667 Köln",
            "vat_id": "DE444555666",
            "description": "Webdesign und Grafik",
            "style": "minimal",
        },
        "T5_MINIMAL": {
            "name": "Einfach GmbH",
            "address": "Kurzstraße 1, 20095 Hamburg",
            "vat_id": "DE777888999",
            "description": "Dienstleistungen",
            "style": "minimal",
        },
    }

    if template_id not in templates_preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    t = templates_preview[template_id]

    # HTML-Vorschau generieren
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Preview: {template_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: auto; }}
            .invoice {{ border: 1px solid #ccc; padding: 20px; background: #fff; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
            .supplier {{ font-weight: bold; font-size: 18px; }}
            .address {{ color: #666; font-size: 12px; }}
            .vat {{ font-size: 11px; color: #888; }}
            .items {{ margin: 20px 0; }}
            .item-row {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; }}
            .totals {{ margin-top: 20px; text-align: right; }}
            .total {{ font-weight: bold; font-size: 18px; }}
        </style>
    </head>
    <body>
        <div class="invoice">
            <div class="header">
                <div class="supplier">{t['name']}</div>
                <div class="address">{t['address']}</div>
                <div class="vat">USt-IdNr.: {t['vat_id']}</div>
            </div>
            <h2>RECHNUNG</h2>
            <p><strong>Rechnungsnummer:</strong> 2025-XXXX</p>
            <p><strong>Datum:</strong> TT.MM.JJJJ</p>
            <div class="items">
                <div class="item-row">
                    <span>{t['description']}</span>
                    <span>XXX,XX €</span>
                </div>
            </div>
            <div class="totals">
                <div>Netto: XXX,XX €</div>
                <div>MwSt. 19%: XX,XX €</div>
                <div class="total">Gesamt: XXX,XX €</div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content, media_type="text/html")


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
    beneficiary_data: dict[str, Any] | None = None,
    project_context: dict[str, Any] | None = None,
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
        beneficiary_data: Optional - Begünstigtendaten für konsistente Rechnungen
            Pflichtfelder: beneficiary_name, street, zip, city
            Optional: legal_form, country, vat_id, aliases
        project_context: Optional - Projektkontext
            Optional: project_id, project_name

    Returns:
        Generator-Job-Info.
    """
    if x_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Validierung der Begünstigtendaten (falls vorhanden)
    if beneficiary_data:
        required_fields = ["beneficiary_name", "street", "zip", "city"]
        missing = [f for f in required_fields if not beneficiary_data.get(f)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required beneficiary fields: {', '.join(missing)}",
            )

        # Keine Dummy-Marker erlaubt
        dummy_markers = ["TEST", "XXX", "DUMMY", "Lorem", "Ipsum", "PLACEHOLDER"]
        for field, value in beneficiary_data.items():
            if isinstance(value, str):
                for marker in dummy_markers:
                    if marker.lower() in value.lower():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Dummy marker '{marker}' found in beneficiary field '{field}'",
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
            "beneficiary_data": beneficiary_data,
            "project_context": project_context,
        },
        status="PENDING",
    )

    session.add(generator_job)
    await session.commit()

    # Celery Task für Generator starten
    task = generate_invoices_task.delay(generator_job.id)

    return {
        "generator_job_id": generator_job.id,
        "status": "RUNNING",
        "output_dir": generator_job.output_dir,
        "solutions_file": generator_job.solutions_file,
        "task_id": task.id,
        "beneficiary_data_used": beneficiary_data is not None,
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

    # Lösungsdatei parsen
    entries = []

    if job.solutions_file:
        solutions_path = Path(job.solutions_file)
        if solutions_path.exists():
            try:
                with open(solutions_path, "r", encoding="utf-8") as f:
                    solutions_data = json.load(f)

                # Einträge formatieren
                for solution in solutions_data:
                    entries.append({
                        "filename": solution.get("filename"),
                        "template": solution.get("template"),
                        "has_error": solution.get("has_error", False),
                        "errors": solution.get("errors", []),
                        "invoice_data": {
                            "invoice_number": solution.get("invoice_number"),
                            "invoice_date": solution.get("invoice_date"),
                            "net_amount": solution.get("net_amount"),
                            "vat_amount": solution.get("vat_amount"),
                            "gross_amount": solution.get("gross_amount"),
                            "vat_rate": solution.get("vat_rate"),
                        },
                    })
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error reading solutions file: {e}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solutions file not found",
            )

    return {
        "solutions_file": job.solutions_file,
        "count": len(entries),
        "entries": entries,
    }
