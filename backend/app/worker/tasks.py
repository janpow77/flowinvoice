# Pfad: /backend/app/worker/tasks.py
"""
FlowAudit Celery Tasks

Hintergrund-Tasks für Dokumentenverarbeitung und Analyse.
"""

import asyncio
import csv
import json
import logging
import random
import shutil
from datetime import UTC, date, datetime, timedelta
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.llm import InvoiceAnalysisRequest, get_llm_adapter
from app.models.document import Document
from app.models.enums import DocumentStatus, Provider
from app.models.export import ExportJob, GeneratorJob
from app.models.project import Project
from app.models.result import AnalysisResult
from app.rag import get_rag_service
from app.services.parser import get_parser
from app.services.rule_engine import get_rule_engine

from .celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def run_async(coro):
    """Führt Coroutine synchron aus (für Celery)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_celery_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Erstellt eine neue Engine und SessionMaker für Celery Tasks.

    Dies ist notwendig, da Celery in separaten Prozessen/Event-Loops läuft
    und die globale Engine nicht kompatibel ist.
    """
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


def _parse_project_period(project: Project | None) -> tuple[date | None, date | None]:
    """
    Parst Projektzeitraum aus Projekt.

    Args:
        project: Projekt-Objekt oder None

    Returns:
        Tuple (project_start, project_end) als date-Objekte
    """
    if not project:
        return None, None

    period = project.project_period
    if not period:
        return None, None

    project_start = None
    project_end = None

    # Start-Datum parsen
    start_str = period.get("start")
    if start_str:
        try:
            if isinstance(start_str, str):
                project_start = datetime.strptime(start_str, "%Y-%m-%d").date()
            elif hasattr(start_str, "date"):
                project_start = start_str.date()
            elif isinstance(start_str, date):
                project_start = start_str
        except (ValueError, AttributeError):
            pass

    # End-Datum parsen
    end_str = period.get("end")
    if end_str:
        try:
            if isinstance(end_str, str):
                project_end = datetime.strptime(end_str, "%Y-%m-%d").date()
            elif hasattr(end_str, "date"):
                project_end = end_str.date()
            elif isinstance(end_str, date):
                project_end = end_str
        except (ValueError, AttributeError):
            pass

    return project_start, project_end


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str) -> dict[str, Any]:
    """
    Verarbeitet Dokument (Parsing + Vorprüfung).

    Args:
        document_id: Dokument-ID

    Returns:
        Dict mit Verarbeitungsergebnis
    """
    logger.info(f"Processing document: {document_id}")

    try:
        result = run_async(_process_document_async(document_id))
        return result

    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {e}")
        self.retry(exc=e, countdown=60)


async def _process_document_async(document_id: str) -> dict[str, Any]:
    """Async-Implementation der Dokumentenverarbeitung."""
    celery_session_maker = get_celery_session_maker()
    async with celery_session_maker() as session:
        # Dokument laden
        document = await session.get(Document, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Status aktualisieren
        document.status = DocumentStatus.PARSING
        await session.commit()

        try:
            # PDF parsen
            parser = get_parser()
            parse_result = parser.parse(document.file_path)

            if parse_result.error:
                document.status = DocumentStatus.ERROR
                document.error_message = parse_result.error
                await session.commit()
                return {"status": "error", "error": parse_result.error}

            # Extrahierte Daten speichern
            document.raw_text = parse_result.raw_text
            document.extracted_data = {
                k: {
                    "value": str(v.value) if v.value else None,
                    "raw_text": v.raw_text,
                    "confidence": v.confidence,
                    "source": v.source,
                }
                for k, v in parse_result.extracted.items()
            }
            document.page_count = len(parse_result.pages)

            # Vorprüfung durchführen
            document.status = DocumentStatus.VALIDATING
            await session.commit()

            # Projekt laden für Zeitraumprüfung
            project = None
            if document.project_id:
                project = await session.get(Project, document.project_id)
            project_start, project_end = _parse_project_period(project)

            rule_engine = get_rule_engine(document.ruleset_id or "DE_USTG")
            precheck = rule_engine.precheck(parse_result, project_start, project_end)

            # Vorprüfungsergebnis speichern
            document.precheck_passed = precheck.passed
            document.precheck_errors = [
                {
                    "feature_id": e.feature_id,
                    "status": e.status.value,
                    "error_type": e.error_type.value if e.error_type else None,
                    "message": e.message,
                    "severity": e.severity.value,
                }
                for e in precheck.errors
            ]

            # Status für nächsten Schritt
            document.status = DocumentStatus.VALIDATED
            await session.commit()

            logger.info(f"Document {document_id} processed successfully")

            return {
                "status": "success",
                "document_id": document_id,
                "pages": len(parse_result.pages),
                "extracted_fields": len(parse_result.extracted),
                "precheck_passed": precheck.passed,
                "error_count": len(precheck.errors),
            }

        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            await session.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def analyze_document_task(
    self,
    document_id: str,
    provider: str = "LOCAL_OLLAMA",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Analysiert Dokument mit LLM.

    Args:
        document_id: Dokument-ID
        provider: LLM-Provider
        model: Modell-ID

    Returns:
        Dict mit Analyseergebnis
    """
    logger.info(f"Analyzing document: {document_id} with {provider}")

    try:
        result = run_async(_analyze_document_async(document_id, provider, model))
        return result

    except Exception as e:
        logger.exception(f"Error analyzing document {document_id}: {e}")
        self.retry(exc=e, countdown=120)


async def _analyze_document_async(
    document_id: str,
    provider_str: str,
    model: str | None,
) -> dict[str, Any]:
    """Async-Implementation der LLM-Analyse."""
    celery_session_maker = get_celery_session_maker()
    async with celery_session_maker() as session:
        # Dokument laden
        document = await session.get(Document, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Provider parsen
        try:
            provider = Provider(provider_str)
        except ValueError:
            provider = Provider.LOCAL_OLLAMA

        # Status aktualisieren
        document.status = DocumentStatus.ANALYZING
        await session.commit()

        try:
            # Parse-Ergebnis rekonstruieren
            parser = get_parser()
            parse_result = parser.parse(document.file_path)

            # Projekt laden für Zeitraumprüfung
            project = None
            if document.project_id:
                project = await session.get(Project, document.project_id)
            project_start, project_end = _parse_project_period(project)

            # Rule Engine für Precheck
            rule_engine = get_rule_engine(document.ruleset_id or "DE_USTG")
            precheck = rule_engine.precheck(parse_result, project_start, project_end)

            # RAG-Kontext holen
            rag_service = get_rag_service()
            rag_context = rag_service.get_context_for_analysis(
                parse_result=parse_result,
                precheck_result=precheck,
            )

            # LLM-Analyse
            llm_adapter = get_llm_adapter()

            analysis_request = InvoiceAnalysisRequest(
                parse_result=parse_result,
                precheck_result=precheck,
                ruleset_id=document.ruleset_id or "DE_USTG",
                rag_examples=[
                    {"content": ex.content, "metadata": ex.metadata}
                    for ex in rag_context.similar_invoices[:3]
                ],
            )

            analysis_result = await llm_adapter.analyze_invoice(
                analysis_request=analysis_request,
                provider_type=provider,
                model=model,
            )

            # Ergebnis speichern
            result = AnalysisResult(
                document_id=document_id,
                provider=provider,
                model=model or llm_adapter.get_provider(provider).default_model,
                semantic_check=analysis_result.semantic_check,
                economic_check=analysis_result.economic_check,
                beneficiary_match=analysis_result.beneficiary_match,
                # Convert warning dicts to strings for ARRAY(String) column
                warnings=[
                    w.get("message", str(w)) if isinstance(w, dict) else str(w)
                    for w in analysis_result.warnings
                ],
                overall_assessment=analysis_result.overall_assessment,
                confidence=analysis_result.confidence,
                input_tokens=analysis_result.llm_response.input_tokens,
                output_tokens=analysis_result.llm_response.output_tokens,
                latency_ms=analysis_result.llm_response.latency_ms,
            )

            session.add(result)
            document.status = DocumentStatus.ANALYZED
            await session.commit()

            logger.info(f"Document {document_id} analyzed successfully")

            return {
                "status": "success",
                "document_id": document_id,
                "result_id": result.id,
                "assessment": analysis_result.overall_assessment,
                "confidence": analysis_result.confidence,
            }

        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            await session.commit()
            raise


# =============================================================================
# PDF Generator Task
# =============================================================================


@celery_app.task(bind=True, max_retries=2)
def generate_invoices_task(
    self,
    generator_job_id: str,
) -> dict[str, Any]:
    """
    Generiert Test-Rechnungen für Seminarbetrieb.

    Args:
        generator_job_id: Generator-Job-ID

    Returns:
        Dict mit Generierungsergebnis
    """
    logger.info(f"Generating invoices for job: {generator_job_id}")

    try:
        result = run_async(_generate_invoices_async(generator_job_id))
        return result

    except Exception as e:
        logger.exception(f"Error generating invoices: {e}")
        self.retry(exc=e, countdown=120)


async def _generate_invoices_async(generator_job_id: str) -> dict[str, Any]:
    """Async-Implementation der Rechnungsgenerierung."""
    celery_session_maker = get_celery_session_maker()
    async with celery_session_maker() as session:
        # Job laden
        job = await session.get(GeneratorJob, generator_job_id)
        if not job:
            raise ValueError(f"Generator job not found: {generator_job_id}")

        job.status = "RUNNING"
        await session.commit()

        try:
            # Konfiguration auslesen
            count = job.count or 20
            templates = job.templates_enabled or ["T1_HANDWERK", "T3_CORPORATE"]
            settings = job.settings or {}

            error_rate = settings.get("error_rate_total", 5.0)
            severity = settings.get("severity", 2)

            # Erweiterte Konfiguration (jetzt tatsächlich verwendet)
            per_feature_error_rates = settings.get("per_feature_error_rates", {})
            alias_noise_probability = settings.get("alias_noise_probability", 10.0)
            date_format_profiles = settings.get("date_format_profiles", ["DD.MM.YYYY"])

            # Begünstigtendaten und Projektkontext aus Settings (optional)
            beneficiary_data = settings.get("beneficiary_data")
            project_context = settings.get("project_context")

            # Ausgabeverzeichnis erstellen
            output_dir = Path(job.output_dir or f"/data/generated/{generator_job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            generated_files: list[str] = []
            solutions: list[dict[str, Any]] = []

            # Rechnungen generieren
            for i in range(count):
                template = random.choice(templates)
                has_error = random.random() * 100 < error_rate

                # Generiere Rechnungsdaten (mit allen Parametern)
                invoice_data = _generate_invoice_data(
                    template=template,
                    index=i + 1,
                    has_error=has_error,
                    severity=severity,
                    ruleset_id=job.ruleset_id,
                    beneficiary_data=beneficiary_data,
                    project_context=project_context,
                    date_format_profiles=date_format_profiles,
                    per_feature_error_rates=per_feature_error_rates,
                    alias_noise_probability=alias_noise_probability,
                )

                # Zufälliger Dateiname
                filename = _generate_random_filename(invoice_data, i + 1)
                filepath = output_dir / filename

                # Rechnung als PDF erstellen und speichern
                _format_invoice_pdf(invoice_data, filepath)

                generated_files.append(str(filepath))

                # Lösung speichern (inkl. Begünstigten-Info)
                solutions.append({
                    "filename": filename,
                    "template": template,
                    "has_error": has_error,
                    "errors": invoice_data.get("injected_errors", []),
                    "correct_values": invoice_data.get("correct_values", {}),
                    "beneficiary_used": invoice_data.get("beneficiary_used", False),
                    "project_id": invoice_data.get("project_id"),
                })

            # Lösungsdatei schreiben
            solutions_file = output_dir / "solutions.json"
            solutions_file.write_text(
                json.dumps(solutions, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            # Fehler-Übersichtsdatei erstellen (für Trainer)
            error_overview_file = output_dir / "fehler_uebersicht.txt"
            error_overview_content = _create_error_overview(solutions, job.ruleset_id or "DE_USTG")
            error_overview_file.write_text(error_overview_content, encoding="utf-8")

            # Job aktualisieren
            job.status = "COMPLETED"
            job.generated_files = generated_files
            job.solutions_file = str(solutions_file)
            await session.commit()

            logger.info(f"Generated {count} invoices for job {generator_job_id}")

            return {
                "status": "success",
                "generator_job_id": generator_job_id,
                "generated_count": len(generated_files),
                "output_dir": str(output_dir),
                "solutions_file": str(solutions_file),
            }

        except Exception:
            job.status = "FAILED"
            await session.commit()
            raise


def _generate_invoice_data(
    template: str,
    index: int,
    has_error: bool,
    severity: int,
    ruleset_id: str,
    beneficiary_data: dict[str, Any] | None = None,
    project_context: dict[str, Any] | None = None,
    date_format_profiles: list[str] | None = None,
    per_feature_error_rates: dict[str, float] | None = None,
    alias_noise_probability: float = 10.0,
) -> dict[str, Any]:
    """
    Generiert Rechnungsdaten basierend auf Template.

    Args:
        template: Template-ID (T1_HANDWERK, etc.)
        index: Laufende Nummer
        has_error: Soll ein Fehler injiziert werden?
        severity: Schweregrad der Fehler (1-5)
        ruleset_id: Aktives Ruleset
        beneficiary_data: Optional - Begünstigtendaten für konsistente Rechnungen
            Pflichtfelder: beneficiary_name, street, zip, city
            Optional: legal_form, country, vat_id, aliases
        project_context: Optional - Projektkontext
            Optional: project_id, project_name
        date_format_profiles: Datumsformate zur Auswahl (z.B. ["DD.MM.YYYY", "YYYY-MM-DD"])
        per_feature_error_rates: Feature-spezifische Fehlerraten
        alias_noise_probability: Wahrscheinlichkeit (%), einen Alias zu verwenden

    Returns:
        Dict mit Rechnungsdaten inkl. ggf. injizierten Fehlern
    """
    # Basisdaten
    today = datetime.now()
    invoice_date = today - timedelta(days=random.randint(1, 30))

    # Datumsformat aus Profilen wählen
    date_formats = date_format_profiles or ["DD.MM.YYYY"]
    date_format = random.choice(date_formats)
    date_format_python = _convert_date_format(date_format)

    # Template-spezifische Daten mit Positionspool
    templates_config = {
        "T1_HANDWERK": {
            "supplier": "Meister Müller Handwerk GmbH",
            "supplier_address": "Werkstraße 12, 80333 München",
            "description": "Reparaturarbeiten und Materialkosten",
            "position_count_range": (3, 12),
            "positions": [
                {"description": "Arbeitsstunden Monteur", "unit": "Std.", "price_range": (45, 85)},
                {"description": "Arbeitsstunden Meister", "unit": "Std.", "price_range": (75, 120)},
                {"description": "Anfahrtspauschale", "unit": "Pausch.", "price_range": (35, 65), "qty_range": (1, 1)},
                {"description": "Kleinmaterial", "unit": "Pausch.", "price_range": (15, 80)},
                {"description": "Kupferrohr 15mm", "unit": "m", "price_range": (8, 15)},
                {"description": "Kupferrohr 22mm", "unit": "m", "price_range": (12, 22)},
                {"description": "Fitting-Set", "unit": "Stk.", "price_range": (5, 25)},
                {"description": "Silikon-Dichtmasse", "unit": "Stk.", "price_range": (8, 18)},
                {"description": "Absperrhahn 1/2\"", "unit": "Stk.", "price_range": (25, 55)},
                {"description": "Wasserhahn Küche", "unit": "Stk.", "price_range": (80, 250)},
                {"description": "Entsorgung Altmaterial", "unit": "Pausch.", "price_range": (25, 75), "qty_range": (1, 1)},
                {"description": "Dichtungsring-Set", "unit": "Stk.", "price_range": (3, 12)},
                {"description": "Flexschlauch", "unit": "Stk.", "price_range": (15, 35)},
                {"description": "Heizungsthermostat", "unit": "Stk.", "price_range": (35, 95)},
            ],
        },
        "T2_SUPERMARKT": {
            "supplier": "Frisch & Gut Lebensmittel",
            "supplier_address": "Marktplatz 1, 10115 Berlin",
            "description": "Lebensmittel und Getränke für Veranstaltung",
            "position_count_range": (5, 20),
            "positions": [
                {"description": "Mineralwasser 1,0L", "unit": "Kiste", "price_range": (6, 10)},
                {"description": "Orangensaft 1L", "unit": "Stk.", "price_range": (2, 4)},
                {"description": "Kaffee gemahlen 500g", "unit": "Pkg.", "price_range": (5, 12)},
                {"description": "Milch 1L", "unit": "Stk.", "price_range": (1, 2)},
                {"description": "Brötchen gemischt", "unit": "Stk.", "price_range": (0.4, 0.8)},
                {"description": "Butter 250g", "unit": "Stk.", "price_range": (2, 4)},
                {"description": "Käse geschnitten 200g", "unit": "Pkg.", "price_range": (3, 6)},
                {"description": "Wurst Aufschnitt 150g", "unit": "Pkg.", "price_range": (2, 5)},
                {"description": "Obst gemischt", "unit": "kg", "price_range": (3, 6)},
                {"description": "Kekse/Gebäck", "unit": "Pkg.", "price_range": (2, 5)},
                {"description": "Servietten 100er", "unit": "Pkg.", "price_range": (2, 4)},
                {"description": "Plastikbecher 50er", "unit": "Pkg.", "price_range": (3, 6)},
            ],
        },
        "T3_CORPORATE": {
            "supplier": "TechSolutions AG",
            "supplier_address": "Innovationsweg 42, 70173 Stuttgart",
            "description": "IT-Beratung und Softwareentwicklung",
            "position_count_range": (3, 8),
            "positions": [
                {"description": "Senior Developer", "unit": "Std.", "price_range": (120, 180)},
                {"description": "Junior Developer", "unit": "Std.", "price_range": (75, 110)},
                {"description": "Projektmanagement", "unit": "Std.", "price_range": (95, 145)},
                {"description": "IT-Consulting", "unit": "Std.", "price_range": (140, 220)},
                {"description": "Code Review", "unit": "Std.", "price_range": (100, 160)},
                {"description": "Systemadministration", "unit": "Std.", "price_range": (85, 130)},
                {"description": "Cloud-Hosting monatlich", "unit": "Monat", "price_range": (200, 800)},
                {"description": "SSL-Zertifikat", "unit": "Jahr", "price_range": (50, 200), "qty_range": (1, 1)},
                {"description": "Domain-Registrierung", "unit": "Jahr", "price_range": (15, 50), "qty_range": (1, 3)},
                {"description": "Softwarelizenz", "unit": "Lizenz", "price_range": (100, 500)},
                {"description": "Datenmigration", "unit": "Pausch.", "price_range": (500, 2000), "qty_range": (1, 1)},
            ],
        },
        "T4_FREELANCER": {
            "supplier": "Max Mustermann",
            "supplier_address": "Homeoffice-Str. 7, 50667 Köln",
            "description": "Freiberufliche Dienstleistungen",
            "position_count_range": (2, 6),
            "positions": [
                {"description": "Konzeption & Planung", "unit": "Std.", "price_range": (65, 95)},
                {"description": "Grafikdesign", "unit": "Std.", "price_range": (55, 85)},
                {"description": "Texterstellung", "unit": "Std.", "price_range": (50, 80)},
                {"description": "Übersetzung DE/EN", "unit": "Wort", "price_range": (0.08, 0.15)},
                {"description": "Lektorat", "unit": "Seite", "price_range": (3, 8)},
                {"description": "Social Media Betreuung", "unit": "Monat", "price_range": (300, 800)},
                {"description": "Fotografie vor Ort", "unit": "Std.", "price_range": (80, 150)},
                {"description": "Bildbearbeitung", "unit": "Bild", "price_range": (15, 45)},
            ],
        },
        "T5_MINIMAL": {
            "supplier": "Schnellservice",
            "supplier_address": "Kurzweg 1, 60311 Frankfurt",
            "description": "Diverse Kleinleistungen",
            "position_count_range": (1, 3),
            "positions": [
                {"description": "Servicepauschale", "unit": "Pausch.", "price_range": (15, 50), "qty_range": (1, 1)},
                {"description": "Kleinreparatur", "unit": "Pausch.", "price_range": (20, 80), "qty_range": (1, 1)},
                {"description": "Arbeitsstunden", "unit": "Std.", "price_range": (30, 55)},
                {"description": "Material", "unit": "Pausch.", "price_range": (10, 40), "qty_range": (1, 1)},
            ],
        },
        "T6_BAUGEWERBE": {
            "supplier": "Baumeister Schmidt Bau GmbH",
            "supplier_address": "Baustraße 45, 40210 Düsseldorf",
            "description": "Baumaßnahmen und Bauleistungen",
            "position_count_range": (8, 35),
            "positions": [
                # Mauerarbeiten
                {"description": "Kalksandstein KS 2DF 240x115x113mm Rohdichte 1,8 für tragende Wände Art.-Nr. 45892", "unit": "Stk.", "price_range": (0.85, 1.45), "qty_range": (100, 2000)},
                {"description": "Porenbeton Planstein PP2-0,40 625x250x150mm Festigkeitsklasse 2 Art.-Nr. 45901", "unit": "Stk.", "price_range": (2.80, 4.20), "qty_range": (50, 500)},
                {"description": "Hochlochziegel HLz 12 240x115x238mm für Außenwände Art.-Nr. 46012", "unit": "Stk.", "price_range": (0.95, 1.65), "qty_range": (200, 3000)},
                {"description": "Mauermörtel M10 40kg Sack Druckfestigkeit 10N/mm² Art.-Nr. 46105", "unit": "Sack", "price_range": (4.50, 7.80), "qty_range": (20, 200)},
                {"description": "Dünnbettmörtel für Plansteine 25kg Sack weiß Art.-Nr. 46108", "unit": "Sack", "price_range": (8.90, 14.50), "qty_range": (10, 100)},
                {"description": "Mauerwerksanker Edelstahl A4 200mm für Verblendmauerwerk Art.-Nr. 46201", "unit": "Stk.", "price_range": (0.45, 0.85), "qty_range": (50, 500)},
                # Betonarbeiten
                {"description": "Transportbeton C25/30 XC2 Körnung 0-16mm Konsistenz F3 Art.-Nr. 47001", "unit": "m³", "price_range": (95, 135)},
                {"description": "Transportbeton C30/37 XC4 WU-Beton wasserundurchlässig Art.-Nr. 47015", "unit": "m³", "price_range": (125, 175)},
                {"description": "Bewehrungsstahl BSt 500 S Ø10mm Stabstahl 12m Länge Art.-Nr. 47102", "unit": "kg", "price_range": (0.95, 1.45), "qty_range": (100, 2000)},
                {"description": "Bewehrungsmatte Q188A 2,30x6,00m Maschenweite 150mm Art.-Nr. 47108", "unit": "Stk.", "price_range": (45, 75), "qty_range": (5, 50)},
                {"description": "Betonschalung Systemschalung 2,70x0,90m Rahmenschalung Art.-Nr. 47205", "unit": "m²", "price_range": (8.50, 14.50)},
                {"description": "Schalungsöl biologisch abbaubar 20L Kanister Art.-Nr. 47210", "unit": "Stk.", "price_range": (65, 95), "qty_range": (1, 10)},
                {"description": "Abstandhalter Kunststoff 25mm für Bewehrung VE 100 Stk. Art.-Nr. 47215", "unit": "VE", "price_range": (12, 22), "qty_range": (5, 50)},
                # Erdarbeiten
                {"description": "Erdaushub Boden Klasse 3-5 maschinell mit Bagger Art.-Nr. 48001", "unit": "m³", "price_range": (18, 35)},
                {"description": "Bodenabtransport inkl. Entsorgung Deponieklasse I Art.-Nr. 48010", "unit": "m³", "price_range": (25, 45)},
                {"description": "Kies-Sand-Gemisch 0/32mm für Tragschicht verdichtet Art.-Nr. 48102", "unit": "m³", "price_range": (28, 48)},
                {"description": "Schotter 32/63mm für Frostschutzschicht Art.-Nr. 48105", "unit": "m³", "price_range": (22, 38)},
                {"description": "Drainage Kies 16/32mm gewaschen für Drainageleitung Art.-Nr. 48108", "unit": "m³", "price_range": (35, 55)},
                {"description": "Geotextil Vlies 150g/m² Rollenware 2,00x50m Art.-Nr. 48201", "unit": "Rolle", "price_range": (85, 145), "qty_range": (1, 10)},
                # Estrich
                {"description": "Zementestrich ZE20 Festigkeitsklasse CT-C25-F4 Art.-Nr. 49001", "unit": "m²", "price_range": (18, 32)},
                {"description": "Calciumsulfatestrich CAF-C30-F5 fließfähig Art.-Nr. 49010", "unit": "m²", "price_range": (22, 38)},
                {"description": "Estrich-Dämmung EPS DEO 30mm WLG 035 Art.-Nr. 49102", "unit": "m²", "price_range": (4.50, 8.20)},
                {"description": "PE-Folie 0,2mm als Trennlage für Estrich Art.-Nr. 49105", "unit": "m²", "price_range": (0.45, 0.85)},
                {"description": "Randdämmstreifen 8x100mm selbstklebend 25m Rolle Art.-Nr. 49108", "unit": "Rolle", "price_range": (12, 22), "qty_range": (2, 20)},
                # Putzarbeiten
                {"description": "Kalkzementputz MG PIII Maschinenputz Unterputz Art.-Nr. 50001", "unit": "m²", "price_range": (8, 15)},
                {"description": "Kalkputz Oberputz gefilzt Körnung 0-1mm Art.-Nr. 50010", "unit": "m²", "price_range": (12, 22)},
                {"description": "Wärmedämmputz WDP mit Perlite 50mm Art.-Nr. 50015", "unit": "m²", "price_range": (28, 48)},
                {"description": "Silikonharzputz Scheibenputz 2mm Außenputz Art.-Nr. 50102", "unit": "m²", "price_range": (18, 32)},
                {"description": "WDVS Mineralwolle-Lamelle 140mm WLG 035 Art.-Nr. 50201", "unit": "m²", "price_range": (45, 75)},
                {"description": "WDVS EPS-Dämmplatte 160mm WLG 032 Art.-Nr. 50205", "unit": "m²", "price_range": (35, 58)},
                {"description": "Armierungsmörtel WDVS mineralisch 25kg Sack Art.-Nr. 50210", "unit": "Sack", "price_range": (18, 32), "qty_range": (10, 100)},
                {"description": "Armierungsgewebe Glasfaser 165g/m² 1x50m Art.-Nr. 50215", "unit": "Rolle", "price_range": (55, 95), "qty_range": (2, 20)},
                # Trockenbau
                {"description": "Gipskartonplatte GKB 12,5mm 2000x1250mm Standard Art.-Nr. 51001", "unit": "Stk.", "price_range": (4.80, 8.50), "qty_range": (20, 200)},
                {"description": "Gipskartonplatte GKFI 12,5mm imprägniert Feuchtraum Art.-Nr. 51005", "unit": "Stk.", "price_range": (7.50, 12.80), "qty_range": (10, 100)},
                {"description": "Gipsfaserplatte 12,5mm 2000x1250mm Fermacell Art.-Nr. 51010", "unit": "Stk.", "price_range": (12, 22), "qty_range": (10, 100)},
                {"description": "CW-Profil 75x50mm 0,6mm verzinkt 4000mm Länge Art.-Nr. 51102", "unit": "Stk.", "price_range": (3.80, 6.50), "qty_range": (20, 200)},
                {"description": "UW-Profil 75x40mm 0,6mm verzinkt 4000mm Länge Art.-Nr. 51105", "unit": "Stk.", "price_range": (3.20, 5.80), "qty_range": (10, 100)},
                {"description": "CD-Profil 60x27mm für Deckenunterkonstruktion Art.-Nr. 51108", "unit": "Stk.", "price_range": (2.80, 4.80), "qty_range": (20, 200)},
                {"description": "Direktabhänger 125mm für CD-Profil VE 100 Stk. Art.-Nr. 51201", "unit": "VE", "price_range": (28, 48), "qty_range": (2, 20)},
                {"description": "Schnellbauschrauben TN 3,5x35mm phosphatiert VE 1000 Art.-Nr. 51205", "unit": "VE", "price_range": (15, 28), "qty_range": (2, 20)},
                {"description": "Mineralwolle Trennwand 60mm WLG 035 Brandschutz Art.-Nr. 51301", "unit": "m²", "price_range": (5.50, 9.80)},
                # Fliesen
                {"description": "Bodenfliese Feinsteinzeug 60x60cm R10 Abrieb 4 Art.-Nr. 52001", "unit": "m²", "price_range": (28, 55)},
                {"description": "Wandfliese Steingut 30x60cm glasiert weiß matt Art.-Nr. 52010", "unit": "m²", "price_range": (18, 35)},
                {"description": "Mosaikfliese Glas 2,5x2,5cm auf Netz 30x30cm Art.-Nr. 52020", "unit": "m²", "price_range": (65, 120)},
                {"description": "Fliesenkleber Flex C2TE S1 25kg für Großformat Art.-Nr. 52101", "unit": "Sack", "price_range": (18, 32), "qty_range": (10, 100)},
                {"description": "Fugenmörtel CG2 WA 5kg Farbe anthrazit Art.-Nr. 52105", "unit": "Stk.", "price_range": (8, 15), "qty_range": (5, 50)},
                {"description": "Abdichtung Flüssigfolie 2K 20kg für Nassräume Art.-Nr. 52201", "unit": "Stk.", "price_range": (125, 195), "qty_range": (1, 10)},
                {"description": "Dichtband selbstklebend 120mm 10m Rolle Art.-Nr. 52205", "unit": "Rolle", "price_range": (22, 38), "qty_range": (2, 20)},
                {"description": "Fliesenkreuze 3mm VE 500 Stk. wiederverwendbar Art.-Nr. 52210", "unit": "VE", "price_range": (8, 15), "qty_range": (2, 20)},
                # Dacharbeiten
                {"description": "Dachziegel Frankfurter Pfanne engobiert rot Art.-Nr. 53001", "unit": "Stk.", "price_range": (0.85, 1.45), "qty_range": (200, 3000)},
                {"description": "Dachstein Braas Tegalit graphit Großformat Art.-Nr. 53010", "unit": "Stk.", "price_range": (2.80, 4.50), "qty_range": (100, 1500)},
                {"description": "Unterspannbahn diffusionsoffen sd<0,3m 1,5x50m Art.-Nr. 53101", "unit": "Rolle", "price_range": (85, 145), "qty_range": (2, 20)},
                {"description": "Dachlatte 30x50mm Fichte/Tanne imprägniert Art.-Nr. 53105", "unit": "lfm", "price_range": (1.20, 2.20), "qty_range": (100, 1000)},
                {"description": "Konterlatte 40x60mm für Hinterlüftung Art.-Nr. 53108", "unit": "lfm", "price_range": (1.80, 3.20), "qty_range": (50, 500)},
                {"description": "Firstziegel Dry-Fix System universal Art.-Nr. 53201", "unit": "Stk.", "price_range": (8, 15), "qty_range": (20, 200)},
                {"description": "Schneefanggitter 2m verzinkt für Pfannenziegel Art.-Nr. 53205", "unit": "Stk.", "price_range": (45, 75), "qty_range": (5, 50)},
                {"description": "Dachfenster Velux GGL CK04 55x98cm Holz weiß Art.-Nr. 53301", "unit": "Stk.", "price_range": (380, 580), "qty_range": (1, 10)},
                {"description": "Eindeckrahmen EDZ für Velux CK04 Ziegel Art.-Nr. 53305", "unit": "Stk.", "price_range": (85, 145), "qty_range": (1, 10)},
                # Zimmererarbeiten
                {"description": "Konstruktionsvollholz KVH 80x160mm C24 NSi Art.-Nr. 54001", "unit": "lfm", "price_range": (8.50, 14.50), "qty_range": (20, 200)},
                {"description": "Brettschichtholz BSH 120x200mm GL24h Art.-Nr. 54010", "unit": "lfm", "price_range": (28, 48), "qty_range": (10, 100)},
                {"description": "OSB-Platte 3 18mm 2500x1250mm für Dachschalung Art.-Nr. 54101", "unit": "Stk.", "price_range": (22, 38), "qty_range": (10, 100)},
                {"description": "Sparrenpfettenanker SPF 170 feuerverzinkt Art.-Nr. 54201", "unit": "Stk.", "price_range": (3.50, 6.20), "qty_range": (20, 200)},
                {"description": "Balkenschuh BSI 60x100 außen feuerverzinkt Art.-Nr. 54205", "unit": "Stk.", "price_range": (4.80, 8.50), "qty_range": (10, 100)},
                {"description": "Holzschutzlasur außen 10L Eimer farblos UV-Schutz Art.-Nr. 54301", "unit": "Stk.", "price_range": (85, 145), "qty_range": (1, 10)},
                # Gerüst und Baustelleneinrichtung
                {"description": "Fassadengerüst Layher Blitz 2,57m Feldlänge Miete Art.-Nr. 55001", "unit": "m²/Monat", "price_range": (6, 12)},
                {"description": "Gerüstmontage/-demontage inkl. Verankerung Art.-Nr. 55005", "unit": "m²", "price_range": (8, 15)},
                {"description": "Bauzaun Mobilzaun 3,50x2,00m Standardelement Miete Art.-Nr. 55101", "unit": "Stk./Monat", "price_range": (8, 15), "qty_range": (10, 100)},
                {"description": "Baucontainer Büro 20ft isoliert Miete Art.-Nr. 55201", "unit": "Monat", "price_range": (250, 450), "qty_range": (1, 6)},
                {"description": "Baucontainer Lager 10ft Miete Art.-Nr. 55205", "unit": "Monat", "price_range": (120, 220), "qty_range": (1, 6)},
                {"description": "Mobile Toilette Miete inkl. Service Art.-Nr. 55210", "unit": "Monat", "price_range": (150, 280), "qty_range": (1, 6)},
                {"description": "Baustromverteiler 63A CEE Miete Art.-Nr. 55301", "unit": "Monat", "price_range": (85, 145), "qty_range": (1, 6)},
                {"description": "Bauschuttcontainer 7m³ inkl. Entsorgung Art.-Nr. 55401", "unit": "Stk.", "price_range": (320, 520), "qty_range": (1, 10)},
                {"description": "Muldencontainer 10m³ für Erdaushub Art.-Nr. 55405", "unit": "Stk.", "price_range": (280, 450), "qty_range": (1, 10)},
                # Arbeitsleistungen
                {"description": "Maurerarbeiten Facharbeiter inkl. Kleingerät Art.-Nr. 56001", "unit": "Std.", "price_range": (48, 68)},
                {"description": "Betonbauer Facharbeiter inkl. Werkzeug Art.-Nr. 56005", "unit": "Std.", "price_range": (52, 72)},
                {"description": "Zimmerer Facharbeiter inkl. Handwerkzeug Art.-Nr. 56010", "unit": "Std.", "price_range": (55, 78)},
                {"description": "Dachdecker Facharbeiter inkl. PSA Art.-Nr. 56015", "unit": "Std.", "price_range": (58, 82)},
                {"description": "Fliesenleger Facharbeiter inkl. Werkzeug Art.-Nr. 56020", "unit": "Std.", "price_range": (52, 75)},
                {"description": "Trockenbauer Facharbeiter inkl. Werkzeug Art.-Nr. 56025", "unit": "Std.", "price_range": (48, 68)},
                {"description": "Bauhelfer ungelernt für Zuarbeiten Art.-Nr. 56030", "unit": "Std.", "price_range": (28, 42)},
                {"description": "Polier/Vorarbeiter Bauleitung vor Ort Art.-Nr. 56035", "unit": "Std.", "price_range": (65, 95)},
                # Geräte und Maschinen
                {"description": "Minibagger 1,8t mit Fahrer Tageseinsatz Art.-Nr. 57001", "unit": "Tag", "price_range": (380, 580)},
                {"description": "Radlader 1,5m³ Schaufel mit Fahrer Art.-Nr. 57005", "unit": "Tag", "price_range": (420, 650)},
                {"description": "Mobilkran 40t Tragkraft inkl. Kranführer Art.-Nr. 57101", "unit": "Einsatz", "price_range": (850, 1450)},
                {"description": "Betonpumpe 24m Reichweite inkl. Bediener Art.-Nr. 57105", "unit": "Einsatz", "price_range": (650, 1050)},
                {"description": "Estrichmaschine Putzmaschine Miete/Tag Art.-Nr. 57201", "unit": "Tag", "price_range": (120, 220)},
                {"description": "Rüttelplatte 400kg vorwärts/rückwärts Miete Art.-Nr. 57205", "unit": "Tag", "price_range": (65, 120)},
                {"description": "Stampfer Vibrationsstampfer 70kg Miete Art.-Nr. 57210", "unit": "Tag", "price_range": (45, 85)},
                {"description": "Kernbohrgerät Ø 50-200mm Miete inkl. Kronen Art.-Nr. 57301", "unit": "Tag", "price_range": (85, 145)},
                {"description": "Aufzug Bauaufzug 200kg Miete/Monat Art.-Nr. 57305", "unit": "Monat", "price_range": (450, 750), "qty_range": (1, 6)},
            ],
        },
        "T7_FORSCHUNG": {
            "supplier": "LabTech Scientific GmbH",
            "supplier_address": "Forschungsallee 12, 69120 Heidelberg",
            "description": "Forschungsausrüstung und Laborgeräte",
            "position_count_range": (8, 35),
            "positions": [
                # Spektroskopie und Analytik
                {"description": "UV-VIS Spektrophotometer Shimadzu UV-1900i Doppelstrahl 190-1100nm Art.-Nr. 60101", "unit": "Stk.", "price_range": (12000, 18500), "qty_range": (1, 2)},
                {"description": "FTIR-Spektrometer Bruker Alpha II ATR-Modul integriert Art.-Nr. 60105", "unit": "Stk.", "price_range": (28000, 45000), "qty_range": (1, 1)},
                {"description": "Fluoreszenzspektrometer Horiba FluoroMax-4 Xenon-Quelle Art.-Nr. 60110", "unit": "Stk.", "price_range": (35000, 55000), "qty_range": (1, 1)},
                {"description": "Raman-Spektrometer Renishaw inVia konfokales System Art.-Nr. 60115", "unit": "Stk.", "price_range": (85000, 145000), "qty_range": (1, 1)},
                {"description": "AAS Atomabsorptionsspektrometer Agilent 240FS AA Art.-Nr. 60120", "unit": "Stk.", "price_range": (45000, 75000), "qty_range": (1, 1)},
                {"description": "ICP-OES Spektrometer Thermo iCAP 7400 Duo Art.-Nr. 60125", "unit": "Stk.", "price_range": (95000, 155000), "qty_range": (1, 1)},
                {"description": "Küvetten Quarzglas SUPRASIL 10mm Schichtdicke 2er Set Art.-Nr. 60201", "unit": "Set", "price_range": (85, 145), "qty_range": (2, 10)},
                {"description": "Küvetten Einweg PS halbmikro 1,5ml VE 100 Stk. Art.-Nr. 60205", "unit": "VE", "price_range": (28, 48), "qty_range": (5, 50)},
                # Mikroskopie
                {"description": "Forschungsmikroskop Zeiss Axio Imager.M2 motorisiert Art.-Nr. 61001", "unit": "Stk.", "price_range": (45000, 85000), "qty_range": (1, 2)},
                {"description": "Stereomikroskop Leica M205 C mit Fluoreszenz Art.-Nr. 61005", "unit": "Stk.", "price_range": (25000, 45000), "qty_range": (1, 2)},
                {"description": "Inversmikroskop Olympus IX73 für Zellkultur Art.-Nr. 61010", "unit": "Stk.", "price_range": (18000, 32000), "qty_range": (1, 2)},
                {"description": "Konfokalmikroskop Nikon A1R HD25 Resonant Scanner Art.-Nr. 61015", "unit": "Stk.", "price_range": (180000, 320000), "qty_range": (1, 1)},
                {"description": "Elektronenmikroskop REM JEOL JSM-IT500HR Art.-Nr. 61020", "unit": "Stk.", "price_range": (250000, 450000), "qty_range": (1, 1)},
                {"description": "Objektiv Plan-Apochromat 63x/1.4 Oil DIC M27 Art.-Nr. 61101", "unit": "Stk.", "price_range": (4500, 7500), "qty_range": (1, 5)},
                {"description": "Objektiv EC Plan-Neofluar 10x/0.30 Ph1 M27 Art.-Nr. 61105", "unit": "Stk.", "price_range": (1200, 2200), "qty_range": (1, 5)},
                {"description": "Kamera Mikroskop sCMOS Hamamatsu ORCA-Flash4.0 V3 Art.-Nr. 61201", "unit": "Stk.", "price_range": (18000, 28000), "qty_range": (1, 3)},
                {"description": "Immersionsöl Typ F 20ml für Fluoreszenz Art.-Nr. 61205", "unit": "Stk.", "price_range": (45, 85), "qty_range": (2, 20)},
                {"description": "Objektträger SuperFrost Plus 76x26mm VE 50 Stk. Art.-Nr. 61210", "unit": "VE", "price_range": (18, 32), "qty_range": (10, 100)},
                {"description": "Deckgläser 24x60mm #1.5H VE 100 Stk. Art.-Nr. 61215", "unit": "VE", "price_range": (25, 45), "qty_range": (5, 50)},
                # Chromatographie
                {"description": "HPLC-System Agilent 1260 Infinity II Quaternär Art.-Nr. 62001", "unit": "Stk.", "price_range": (65000, 95000), "qty_range": (1, 1)},
                {"description": "UHPLC Vanquish Duo Thermo Fisher Scientific Art.-Nr. 62005", "unit": "Stk.", "price_range": (85000, 125000), "qty_range": (1, 1)},
                {"description": "GC-MS System Shimadzu GCMS-QP2020 NX Art.-Nr. 62010", "unit": "Stk.", "price_range": (95000, 145000), "qty_range": (1, 1)},
                {"description": "LC-MS/MS Triple Quad Sciex 6500+ QTRAP Art.-Nr. 62015", "unit": "Stk.", "price_range": (280000, 420000), "qty_range": (1, 1)},
                {"description": "HPLC-Säule C18 Phenomenex Kinetex 2.6µm 150x4.6mm Art.-Nr. 62101", "unit": "Stk.", "price_range": (450, 750), "qty_range": (1, 10)},
                {"description": "HPLC-Säule HILIC Waters BEH Amide 1.7µm 100x2.1mm Art.-Nr. 62105", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 5)},
                {"description": "GC-Säule DB-5ms 30m x 0.25mm x 0.25µm Art.-Nr. 62110", "unit": "Stk.", "price_range": (380, 620), "qty_range": (1, 5)},
                {"description": "Vorsäule SecurityGuard C18 4x3mm VE 4 Stk. Art.-Nr. 62115", "unit": "VE", "price_range": (185, 320), "qty_range": (2, 10)},
                {"description": "HPLC-Vials 2ml Klarglas mit Septum VE 100 Stk. Art.-Nr. 62201", "unit": "VE", "price_range": (65, 120), "qty_range": (5, 50)},
                {"description": "GC-Vials 1.5ml Crimp mit Mikroeinsatz VE 100 Art.-Nr. 62205", "unit": "VE", "price_range": (85, 145), "qty_range": (5, 50)},
                # Zentrifugen und Probenvorbereitung
                {"description": "Ultrazentrifuge Beckman Optima XPN-100 100.000 rpm Art.-Nr. 63001", "unit": "Stk.", "price_range": (85000, 145000), "qty_range": (1, 1)},
                {"description": "Hochgeschwindigkeitszentrifuge Sorvall LYNX 6000 Art.-Nr. 63005", "unit": "Stk.", "price_range": (28000, 48000), "qty_range": (1, 2)},
                {"description": "Tischzentrifuge Eppendorf 5425 R gekühlt 15000rpm Art.-Nr. 63010", "unit": "Stk.", "price_range": (8500, 14500), "qty_range": (1, 5)},
                {"description": "Mikrozentrifuge Eppendorf MiniSpin Plus 14500rpm Art.-Nr. 63015", "unit": "Stk.", "price_range": (2800, 4800), "qty_range": (1, 5)},
                {"description": "Rotor Festwinkel FA-45-30-11 für 5425 Art.-Nr. 63101", "unit": "Stk.", "price_range": (1800, 3200), "qty_range": (1, 3)},
                {"description": "Rotor Ausschwing A-4-62 für 5910 R Art.-Nr. 63105", "unit": "Stk.", "price_range": (2500, 4200), "qty_range": (1, 3)},
                {"description": "Zentrifugenröhrchen 50ml Falcon konisch VE 500 Art.-Nr. 63201", "unit": "VE", "price_range": (85, 145), "qty_range": (5, 50)},
                {"description": "Zentrifugenröhrchen 15ml Falcon konisch VE 500 Art.-Nr. 63205", "unit": "VE", "price_range": (65, 115), "qty_range": (5, 50)},
                {"description": "PCR-Röhrchen 0.2ml Einzelgefäße VE 1000 Art.-Nr. 63210", "unit": "VE", "price_range": (45, 85), "qty_range": (5, 50)},
                # Waagen und Messgeräte
                {"description": "Analysenwaage Sartorius Quintix 224-1S 220g/0.1mg Art.-Nr. 64001", "unit": "Stk.", "price_range": (3500, 5800), "qty_range": (1, 3)},
                {"description": "Präzisionswaage Mettler Toledo XSR6002S 6100g/0.01g Art.-Nr. 64005", "unit": "Stk.", "price_range": (4800, 7500), "qty_range": (1, 3)},
                {"description": "Mikrowaage Sartorius Cubis II 6.1g/0.001mg Art.-Nr. 64010", "unit": "Stk.", "price_range": (18000, 32000), "qty_range": (1, 2)},
                {"description": "pH-Meter Mettler Toledo SevenExcellence S400 Art.-Nr. 64101", "unit": "Stk.", "price_range": (2800, 4500), "qty_range": (1, 5)},
                {"description": "pH-Elektrode InLab Expert Pro-ISM Art.-Nr. 64105", "unit": "Stk.", "price_range": (380, 620), "qty_range": (1, 10)},
                {"description": "Leitfähigkeitsmessgerät WTW Cond 3310 IDS Art.-Nr. 64110", "unit": "Stk.", "price_range": (1200, 2200), "qty_range": (1, 3)},
                {"description": "Sauerstoffsensor optisch Hamilton VisiFerm DO Art.-Nr. 64115", "unit": "Stk.", "price_range": (1800, 3200), "qty_range": (1, 5)},
                {"description": "Refraktometer digital Krüss DR6300-T Art.-Nr. 64120", "unit": "Stk.", "price_range": (4500, 7500), "qty_range": (1, 2)},
                {"description": "Viskosimeter Brookfield DV2T Touch Screen Art.-Nr. 64125", "unit": "Stk.", "price_range": (8500, 14500), "qty_range": (1, 2)},
                # Temperierung und Inkubation
                {"description": "CO2-Inkubator Thermo Heracell VIOS 160i 165L Art.-Nr. 65001", "unit": "Stk.", "price_range": (12000, 22000), "qty_range": (1, 3)},
                {"description": "Inkubationsschüttler Infors HT Multitron Standard Art.-Nr. 65005", "unit": "Stk.", "price_range": (18000, 32000), "qty_range": (1, 2)},
                {"description": "Brutschrank Memmert IN110 108L natürliche Konvektion Art.-Nr. 65010", "unit": "Stk.", "price_range": (2800, 4800), "qty_range": (1, 5)},
                {"description": "Trockenschrank Binder FED 115 115L bis 300°C Art.-Nr. 65015", "unit": "Stk.", "price_range": (3500, 5800), "qty_range": (1, 3)},
                {"description": "Wasserbad Julabo CORIO C-BT19 19L bis 99.9°C Art.-Nr. 65101", "unit": "Stk.", "price_range": (1800, 3200), "qty_range": (1, 5)},
                {"description": "Thermoblock Eppendorf ThermoMixer C mit Smartblock Art.-Nr. 65105", "unit": "Stk.", "price_range": (2500, 4200), "qty_range": (1, 5)},
                {"description": "Kryostat Julabo FP50-ME -50 bis +200°C Art.-Nr. 65110", "unit": "Stk.", "price_range": (8500, 14500), "qty_range": (1, 2)},
                {"description": "Magnetrührer IKA RCT digital mit Heizung Art.-Nr. 65201", "unit": "Stk.", "price_range": (850, 1450), "qty_range": (1, 10)},
                {"description": "Überkopfschüttler Heidolph Reax 20/12 Art.-Nr. 65205", "unit": "Stk.", "price_range": (2200, 3800), "qty_range": (1, 3)},
                {"description": "Vortex-Mixer IKA Vortex 3 mit Aufsätzen Art.-Nr. 65210", "unit": "Stk.", "price_range": (450, 780), "qty_range": (1, 10)},
                # Kühlung und Lagerung
                {"description": "Ultratiefkühlschrank Thermo TSX -86°C 702L Art.-Nr. 66001", "unit": "Stk.", "price_range": (18000, 32000), "qty_range": (1, 2)},
                {"description": "Laborkühlschrank Liebherr LKPv 6523 601L +1 bis +15°C Art.-Nr. 66005", "unit": "Stk.", "price_range": (3500, 5800), "qty_range": (1, 3)},
                {"description": "Labortiefkühlschrank Liebherr LGPv 6520 601L -30°C Art.-Nr. 66010", "unit": "Stk.", "price_range": (5500, 8500), "qty_range": (1, 3)},
                {"description": "Flüssigstickstoff-Lagertank MVE CryoSystem 6000 Art.-Nr. 66015", "unit": "Stk.", "price_range": (8500, 14500), "qty_range": (1, 2)},
                {"description": "Kryoboxen Karton 81 Plätze für 1.5ml VE 50 Art.-Nr. 66101", "unit": "VE", "price_range": (85, 145), "qty_range": (2, 20)},
                {"description": "Kryoröhrchen 2ml steril mit Gewinde VE 500 Art.-Nr. 66105", "unit": "VE", "price_range": (125, 220), "qty_range": (2, 20)},
                # Sterilisation und Reinraum
                {"description": "Autoklav Systec VX-150 150L Tischautoklav Art.-Nr. 67001", "unit": "Stk.", "price_range": (22000, 38000), "qty_range": (1, 2)},
                {"description": "Sicherheitswerkbank Thermo Safe 2020 Klasse II Art.-Nr. 67005", "unit": "Stk.", "price_range": (12000, 22000), "qty_range": (1, 3)},
                {"description": "Laminar Flow Clean Bench 1.2m horizontal Art.-Nr. 67010", "unit": "Stk.", "price_range": (6500, 11000), "qty_range": (1, 3)},
                {"description": "UV-Sterilisationsschrank 100L mit Timer Art.-Nr. 67015", "unit": "Stk.", "price_range": (1800, 3200), "qty_range": (1, 3)},
                {"description": "Autoklavierbeutel 600x780mm VE 100 Stk. Art.-Nr. 67101", "unit": "VE", "price_range": (45, 85), "qty_range": (5, 50)},
                {"description": "Indikatorband Autoklavierung 19mm x 50m Art.-Nr. 67105", "unit": "Rolle", "price_range": (12, 25), "qty_range": (5, 50)},
                # Pipettieren und Dosieren
                {"description": "Pipette Eppendorf Research plus 0.5-10µl Art.-Nr. 68001", "unit": "Stk.", "price_range": (320, 520), "qty_range": (1, 20)},
                {"description": "Pipette Eppendorf Research plus 10-100µl Art.-Nr. 68005", "unit": "Stk.", "price_range": (320, 520), "qty_range": (1, 20)},
                {"description": "Pipette Eppendorf Research plus 100-1000µl Art.-Nr. 68010", "unit": "Stk.", "price_range": (320, 520), "qty_range": (1, 20)},
                {"description": "Mehrkanalpipette 8-Kanal 30-300µl Research plus Art.-Nr. 68015", "unit": "Stk.", "price_range": (750, 1250), "qty_range": (1, 10)},
                {"description": "Pipettenspitzen 10µl mit Filter steril VE 960 Art.-Nr. 68101", "unit": "VE", "price_range": (85, 145), "qty_range": (5, 100)},
                {"description": "Pipettenspitzen 200µl mit Filter steril VE 960 Art.-Nr. 68105", "unit": "VE", "price_range": (75, 125), "qty_range": (5, 100)},
                {"description": "Pipettenspitzen 1000µl mit Filter steril VE 960 Art.-Nr. 68110", "unit": "VE", "price_range": (95, 165), "qty_range": (5, 100)},
                {"description": "Pipettierhilfe Pipetboy acu 2 Akku Art.-Nr. 68201", "unit": "Stk.", "price_range": (450, 780), "qty_range": (1, 10)},
                {"description": "Serologische Pipetten 10ml steril VE 200 Art.-Nr. 68205", "unit": "VE", "price_range": (55, 95), "qty_range": (5, 50)},
                # Laborglas und Verbrauchsmaterial
                {"description": "Erlenmeyerkolben 500ml Borosilikat NS 29/32 Art.-Nr. 69001", "unit": "Stk.", "price_range": (12, 25), "qty_range": (5, 50)},
                {"description": "Becherglas 1000ml Borosilikat hohe Form Art.-Nr. 69005", "unit": "Stk.", "price_range": (8, 18), "qty_range": (5, 50)},
                {"description": "Messkolben 100ml Klasse A mit NS 14/23 Art.-Nr. 69010", "unit": "Stk.", "price_range": (18, 35), "qty_range": (5, 50)},
                {"description": "Vollpipette 10ml Klasse AS 1 Markierung Art.-Nr. 69015", "unit": "Stk.", "price_range": (8, 15), "qty_range": (5, 50)},
                {"description": "Bürette 50ml Klasse AS mit Schellbach-Streifen Art.-Nr. 69020", "unit": "Stk.", "price_range": (85, 145), "qty_range": (2, 20)},
                {"description": "Petrischalen Glas 100mm Ø sterilisierbar Art.-Nr. 69101", "unit": "Stk.", "price_range": (4, 8), "qty_range": (20, 200)},
                {"description": "Petrischalen PS steril 90mm VE 500 Art.-Nr. 69105", "unit": "VE", "price_range": (65, 115), "qty_range": (2, 20)},
                {"description": "Reaktionsgefäße 1.5ml Safe-Lock VE 1000 Art.-Nr. 69110", "unit": "VE", "price_range": (45, 85), "qty_range": (5, 50)},
                {"description": "Reaktionsgefäße 2.0ml Safe-Lock VE 1000 Art.-Nr. 69115", "unit": "VE", "price_range": (55, 95), "qty_range": (5, 50)},
                {"description": "Schraubdeckelgefäße 50ml PP steril VE 300 Art.-Nr. 69120", "unit": "VE", "price_range": (125, 220), "qty_range": (2, 20)},
                # Services
                {"description": "Kalibrierung Waage DAkkS-akkreditiert Art.-Nr. 70001", "unit": "Gerät", "price_range": (180, 320)},
                {"description": "Kalibrierung Pipetten ISO 8655 3 Volumina Art.-Nr. 70005", "unit": "Gerät", "price_range": (45, 85)},
                {"description": "Wartung HPLC-System Jahresinspektion Art.-Nr. 70010", "unit": "Einsatz", "price_range": (850, 1450), "qty_range": (1, 2)},
                {"description": "IQ/OQ Qualifizierung Dokumentation Art.-Nr. 70015", "unit": "Gerät", "price_range": (450, 850)},
                {"description": "Einweisung Gerätebedienung vor Ort pro Std. Art.-Nr. 70101", "unit": "Std.", "price_range": (120, 220)},
                {"description": "Methodenentwicklung HPLC pro Tag Art.-Nr. 70105", "unit": "Tag", "price_range": (850, 1450)},
            ],
        },
        "T8_IT_HARDWARE": {
            "supplier": "CompuTech Systems AG",
            "supplier_address": "Digitalweg 8, 85748 Garching",
            "description": "IT-Hardware und Computersysteme",
            "position_count_range": (8, 35),
            "positions": [
                # Desktop-PCs und Workstations
                {"description": "Dell OptiPlex 7010 Tower Intel Core i7-13700 16GB 512GB SSD Win11 Pro Art.-Nr. 80101", "unit": "Stk.", "price_range": (1250, 1650), "qty_range": (1, 50)},
                {"description": "HP ProDesk 400 G9 SFF Intel Core i5-13500 8GB 256GB SSD Win11 Pro Art.-Nr. 80105", "unit": "Stk.", "price_range": (780, 1050), "qty_range": (1, 100)},
                {"description": "Lenovo ThinkStation P360 Tower Xeon W-1370 32GB 1TB SSD RTX A2000 Art.-Nr. 80110", "unit": "Stk.", "price_range": (2450, 3250), "qty_range": (1, 20)},
                {"description": "Apple Mac Studio M2 Max 32GB 512GB SSD Space Grau Art.-Nr. 80115", "unit": "Stk.", "price_range": (2250, 2650), "qty_range": (1, 10)},
                {"description": "Dell Precision 3680 Tower Intel Core i9-14900K 64GB 2TB NVMe RTX 4080 Art.-Nr. 80120", "unit": "Stk.", "price_range": (4850, 6250), "qty_range": (1, 10)},
                {"description": "HP Z4 G5 Workstation Xeon W5-2455X 128GB ECC 4TB NVMe RTX A5000 Art.-Nr. 80125", "unit": "Stk.", "price_range": (8500, 12500), "qty_range": (1, 5)},
                # Notebooks
                {"description": "Lenovo ThinkPad T14s Gen4 AMD Ryzen 7 PRO 7840U 16GB 512GB 14\" WUXGA Art.-Nr. 81001", "unit": "Stk.", "price_range": (1450, 1850), "qty_range": (1, 50)},
                {"description": "Dell Latitude 5540 Intel Core i5-1345U 16GB 256GB 15.6\" FHD Art.-Nr. 81005", "unit": "Stk.", "price_range": (1050, 1380), "qty_range": (1, 100)},
                {"description": "HP EliteBook 840 G10 Intel Core i7-1365U 32GB 512GB 14\" WUXGA Art.-Nr. 81010", "unit": "Stk.", "price_range": (1650, 2150), "qty_range": (1, 50)},
                {"description": "Apple MacBook Pro 14\" M3 Pro 18GB 512GB Space Grau Art.-Nr. 81015", "unit": "Stk.", "price_range": (2250, 2650), "qty_range": (1, 20)},
                {"description": "Lenovo ThinkPad P16v Gen1 Intel Core i7-13700H 32GB 1TB RTX A1000 16\" Art.-Nr. 81020", "unit": "Stk.", "price_range": (2450, 3150), "qty_range": (1, 20)},
                {"description": "Dell Precision 5680 Intel Core i9-13900H 64GB 2TB RTX 3500 Ada 16\" OLED Art.-Nr. 81025", "unit": "Stk.", "price_range": (4850, 6850), "qty_range": (1, 10)},
                {"description": "Microsoft Surface Pro 9 Intel Core i7 16GB 256GB 13\" PixelSense inkl. Tastatur Art.-Nr. 81030", "unit": "Stk.", "price_range": (1650, 2150), "qty_range": (1, 30)},
                # Monitore
                {"description": "Dell UltraSharp U2723QE 27\" 4K IPS USB-C Hub 90W PD Art.-Nr. 82001", "unit": "Stk.", "price_range": (650, 850), "qty_range": (1, 100)},
                {"description": "LG 27UK850-W 27\" 4K UHD IPS HDR10 USB-C Pivot Art.-Nr. 82005", "unit": "Stk.", "price_range": (480, 650), "qty_range": (1, 100)},
                {"description": "Samsung ViewFinity S80PB 32\" 4K UHD VA USB-C 90W PD Art.-Nr. 82010", "unit": "Stk.", "price_range": (550, 750), "qty_range": (1, 50)},
                {"description": "Dell UltraSharp U3423WE 34\" WQHD Curved IPS USB-C Hub Art.-Nr. 82015", "unit": "Stk.", "price_range": (950, 1250), "qty_range": (1, 30)},
                {"description": "EIZO FlexScan EV2795 27\" WQHD IPS USB-C Daisy Chain Art.-Nr. 82020", "unit": "Stk.", "price_range": (850, 1150), "qty_range": (1, 50)},
                {"description": "BenQ PD3220U 32\" 4K UHD IPS Thunderbolt 3 für Designer Art.-Nr. 82025", "unit": "Stk.", "price_range": (1250, 1650), "qty_range": (1, 20)},
                {"description": "Apple Studio Display 27\" 5K Retina Nanotexturglas höhenverstellbar Art.-Nr. 82030", "unit": "Stk.", "price_range": (1950, 2350), "qty_range": (1, 10)},
                {"description": "Dell UltraSharp U4924DW 49\" DQHD Curved IPS USB-C 90W PD Art.-Nr. 82035", "unit": "Stk.", "price_range": (1450, 1850), "qty_range": (1, 20)},
                # Server und Storage
                {"description": "Dell PowerEdge R660xs 2HE Xeon Silver 4410Y 32GB 2x480GB SSD RAID Art.-Nr. 83001", "unit": "Stk.", "price_range": (4850, 6850), "qty_range": (1, 10)},
                {"description": "HPE ProLiant DL380 Gen11 2HE Xeon Gold 5415+ 64GB 4x1.2TB SAS Art.-Nr. 83005", "unit": "Stk.", "price_range": (8500, 12500), "qty_range": (1, 5)},
                {"description": "Lenovo ThinkSystem SR650 V3 2HE Xeon Platinum 8460Y+ 128GB 8x2.4TB NVMe Art.-Nr. 83010", "unit": "Stk.", "price_range": (18500, 28500), "qty_range": (1, 3)},
                {"description": "Synology RackStation RS1221RP+ 8-Bay NAS Ryzen V1500B 4GB ECC Redundant PSU Art.-Nr. 83101", "unit": "Stk.", "price_range": (1450, 1950), "qty_range": (1, 10)},
                {"description": "QNAP TS-h1290FX-7302P 12-Bay NAS AMD EPYC 64GB 2x10GbE Art.-Nr. 83105", "unit": "Stk.", "price_range": (4850, 6850), "qty_range": (1, 5)},
                {"description": "NetApp AFF A250 All-Flash Storage Controller Paar inkl. Support Art.-Nr. 83110", "unit": "Stk.", "price_range": (35000, 55000), "qty_range": (1, 2)},
                {"description": "HPE MSA 2062 12Gb SAS SFF Storage Dual Controller 24x1.92TB SSD Art.-Nr. 83115", "unit": "Stk.", "price_range": (28000, 42000), "qty_range": (1, 3)},
                # Speichermedien
                {"description": "Samsung 990 PRO 2TB NVMe M.2 PCIe 4.0 7450MB/s Art.-Nr. 84001", "unit": "Stk.", "price_range": (165, 220), "qty_range": (1, 100)},
                {"description": "WD Red Plus 8TB NAS HDD 3.5\" SATA 256MB Cache CMR Art.-Nr. 84005", "unit": "Stk.", "price_range": (185, 250), "qty_range": (1, 100)},
                {"description": "Seagate Exos X20 20TB Enterprise HDD 3.5\" SATA 256MB 7200rpm Art.-Nr. 84010", "unit": "Stk.", "price_range": (380, 520), "qty_range": (1, 50)},
                {"description": "Kingston KC3000 4TB NVMe M.2 PCIe 4.0 7000MB/s Art.-Nr. 84015", "unit": "Stk.", "price_range": (320, 450), "qty_range": (1, 50)},
                {"description": "Samsung 870 EVO 4TB SATA SSD 2.5\" 560MB/s Art.-Nr. 84020", "unit": "Stk.", "price_range": (280, 380), "qty_range": (1, 50)},
                {"description": "Micron 7450 PRO 3.84TB NVMe U.3 Enterprise SSD Art.-Nr. 84025", "unit": "Stk.", "price_range": (450, 650), "qty_range": (1, 50)},
                {"description": "HPE 1.92TB SATA MU SFF SC PM897 SSD für ProLiant Art.-Nr. 84030", "unit": "Stk.", "price_range": (480, 680), "qty_range": (1, 30)},
                # Arbeitsspeicher
                {"description": "Kingston FURY Beast DDR5-5600 32GB (2x16GB) CL36 AMD EXPO Art.-Nr. 84101", "unit": "Kit", "price_range": (125, 175), "qty_range": (1, 100)},
                {"description": "Crucial DDR5-4800 64GB (2x32GB) ECC UDIMM für Workstation Art.-Nr. 84105", "unit": "Kit", "price_range": (280, 420), "qty_range": (1, 50)},
                {"description": "Samsung DDR5-4800 128GB (4x32GB) ECC RDIMM für Server Art.-Nr. 84110", "unit": "Kit", "price_range": (650, 950), "qty_range": (1, 30)},
                {"description": "Kingston Server Premier DDR4-3200 256GB (8x32GB) ECC RDIMM Art.-Nr. 84115", "unit": "Kit", "price_range": (850, 1250), "qty_range": (1, 20)},
                {"description": "Corsair Vengeance DDR5-6000 32GB (2x16GB) CL30 XMP Art.-Nr. 84120", "unit": "Kit", "price_range": (145, 195), "qty_range": (1, 100)},
                # Netzwerk-Switches
                {"description": "Cisco Catalyst C9200L-24P-4G-E 24-Port PoE+ 4x1G SFP L3 Switch Art.-Nr. 85001", "unit": "Stk.", "price_range": (2850, 3850), "qty_range": (1, 20)},
                {"description": "HPE Aruba 6300M 24-Port PoE+ 4SFP56 L3 Managed Switch Art.-Nr. 85005", "unit": "Stk.", "price_range": (4850, 6850), "qty_range": (1, 10)},
                {"description": "Ubiquiti UniFi USW-Pro-48-PoE 48-Port PoE+ L3 Managed Switch Art.-Nr. 85010", "unit": "Stk.", "price_range": (950, 1350), "qty_range": (1, 20)},
                {"description": "Netgear MS510TXPP 8-Port Multi-Gig PoE+ Smart Switch 2x10G SFP+ Art.-Nr. 85015", "unit": "Stk.", "price_range": (480, 680), "qty_range": (1, 30)},
                {"description": "MikroTik CRS326-24G-2S+RM 24-Port Gigabit 2x10G SFP+ Cloud Router Art.-Nr. 85020", "unit": "Stk.", "price_range": (220, 320), "qty_range": (1, 50)},
                {"description": "Juniper EX4100-48P 48-Port PoE+ 4x10G SFP+ L3 Switch Art.-Nr. 85025", "unit": "Stk.", "price_range": (5850, 7850), "qty_range": (1, 10)},
                # WLAN und Access Points
                {"description": "Cisco Catalyst 9136I Wi-Fi 6E Access Point 4x4:4 OFDMA Art.-Nr. 85101", "unit": "Stk.", "price_range": (1250, 1750), "qty_range": (1, 50)},
                {"description": "Ubiquiti UniFi U6 Enterprise WiFi 6E Access Point 2.5GbE Art.-Nr. 85105", "unit": "Stk.", "price_range": (380, 520), "qty_range": (1, 100)},
                {"description": "HPE Aruba AP-635 Wi-Fi 6E Tri-Radio Access Point Art.-Nr. 85110", "unit": "Stk.", "price_range": (850, 1250), "qty_range": (1, 30)},
                {"description": "Ruckus R750 Wi-Fi 6 4x4:4 MU-MIMO Access Point Art.-Nr. 85115", "unit": "Stk.", "price_range": (950, 1350), "qty_range": (1, 30)},
                {"description": "Fortinet FortiAP 431G Wi-Fi 6E Tri-Radio Outdoor AP Art.-Nr. 85120", "unit": "Stk.", "price_range": (1450, 1950), "qty_range": (1, 20)},
                # Firewall und Security
                {"description": "Fortinet FortiGate 60F Next-Gen Firewall 10Gbps FW 700Mbps IPS Art.-Nr. 85201", "unit": "Stk.", "price_range": (850, 1250), "qty_range": (1, 20)},
                {"description": "Sophos XGS 2100 Firewall Appliance inkl. 1 Jahr FullGuard Art.-Nr. 85205", "unit": "Stk.", "price_range": (2850, 3850), "qty_range": (1, 10)},
                {"description": "Palo Alto PA-440 Next-Gen Firewall inkl. Subscription Art.-Nr. 85210", "unit": "Stk.", "price_range": (1850, 2650), "qty_range": (1, 10)},
                {"description": "Cisco Meraki MX68 Cloud-Managed Security Appliance Art.-Nr. 85215", "unit": "Stk.", "price_range": (950, 1450), "qty_range": (1, 20)},
                # USV und Stromversorgung
                {"description": "APC Smart-UPS SMT1500RMI2UC 1500VA 1000W LCD RM 2HE USB Art.-Nr. 86001", "unit": "Stk.", "price_range": (850, 1150), "qty_range": (1, 20)},
                {"description": "Eaton 5PX 3000VA 2700W Line-Interactive UPS RM 2HE Art.-Nr. 86005", "unit": "Stk.", "price_range": (1450, 1950), "qty_range": (1, 10)},
                {"description": "APC Smart-UPS SRT6KRMXLI 6000VA 6000W Online RM 4HE Art.-Nr. 86010", "unit": "Stk.", "price_range": (4850, 6850), "qty_range": (1, 5)},
                {"description": "Vertiv Liebert GXT5 10kVA 10kW Online UPS inkl. Batterie Art.-Nr. 86015", "unit": "Stk.", "price_range": (6850, 9850), "qty_range": (1, 3)},
                {"description": "APC AP8853 Rack PDU Switched 16A 21xC13 3xC19 Art.-Nr. 86101", "unit": "Stk.", "price_range": (950, 1350), "qty_range": (1, 20)},
                {"description": "Raritan PX3-5902V Intelligent PDU 32A 24xC13 6xC19 Art.-Nr. 86105", "unit": "Stk.", "price_range": (1450, 1950), "qty_range": (1, 10)},
                # Kabel und Verkabelung
                {"description": "LAN-Kabel CAT-5e Patchkabel RJ45 5,0m grau für Netzwerke Art.-Nr. 87001", "unit": "Stk.", "price_range": (2.80, 4.50), "qty_range": (10, 500)},
                {"description": "LAN-Kabel CAT-6 Patchkabel RJ45 10,0m blau S/FTP PiMF Art.-Nr. 87005", "unit": "Stk.", "price_range": (5.50, 8.50), "qty_range": (10, 500)},
                {"description": "LAN-Kabel CAT-6a Patchkabel RJ45 3,0m gelb S/FTP 10GbE Art.-Nr. 87010", "unit": "Stk.", "price_range": (4.80, 7.50), "qty_range": (10, 500)},
                {"description": "LAN-Kabel CAT-7 Patchkabel RJ45 15,0m schwarz S/FTP 600MHz Art.-Nr. 87015", "unit": "Stk.", "price_range": (12.50, 18.50), "qty_range": (5, 200)},
                {"description": "LAN-Kabel CAT-8 Patchkabel RJ45 2,0m rot S/FTP 40GbE 2000MHz Art.-Nr. 87020", "unit": "Stk.", "price_range": (8.50, 14.50), "qty_range": (5, 200)},
                {"description": "Glasfaser-Patchkabel LC/LC OM4 Duplex 50/125µm 5m violett Art.-Nr. 87101", "unit": "Stk.", "price_range": (12.50, 22.50), "qty_range": (5, 100)},
                {"description": "Glasfaser-Patchkabel LC/SC OS2 Duplex 9/125µm 10m gelb Art.-Nr. 87105", "unit": "Stk.", "price_range": (15.50, 25.50), "qty_range": (5, 100)},
                {"description": "DAC-Kabel SFP+ 10G Direct Attach Copper 3m passiv Art.-Nr. 87110", "unit": "Stk.", "price_range": (25, 45), "qty_range": (5, 50)},
                {"description": "DAC-Kabel QSFP28 100G Direct Attach Copper 2m passiv Art.-Nr. 87115", "unit": "Stk.", "price_range": (65, 120), "qty_range": (2, 30)},
                {"description": "Verlegekabel CAT-7 S/FTP 4x2xAWG23 LSZH 1000m Trommel Art.-Nr. 87201", "unit": "Stk.", "price_range": (380, 580), "qty_range": (1, 10)},
                {"description": "Verlegekabel CAT-6a U/FTP 4x2xAWG23 LSZH 500m Karton Art.-Nr. 87205", "unit": "Stk.", "price_range": (250, 380), "qty_range": (1, 20)},
                {"description": "Patchpanel 24-Port CAT-6a geschirmt 1HE 19\" schwarz Art.-Nr. 87301", "unit": "Stk.", "price_range": (85, 145), "qty_range": (1, 50)},
                {"description": "Keystone-Modul CAT-6a RJ45 geschirmt werkzeuglos VE 24 Art.-Nr. 87305", "unit": "VE", "price_range": (125, 195), "qty_range": (1, 50)},
                {"description": "Netzwerkdose Aufputz 2-fach CAT-6a geschirmt reinweiß Art.-Nr. 87310", "unit": "Stk.", "price_range": (18, 32), "qty_range": (10, 200)},
                # Eingabegeräte und Peripherie
                {"description": "Logitech MX Keys S Wireless Tastatur Bluetooth USB-C deutsch Art.-Nr. 88001", "unit": "Stk.", "price_range": (95, 135), "qty_range": (1, 100)},
                {"description": "Microsoft Sculpt Ergonomic Desktop Set Tastatur + Maus wireless Art.-Nr. 88005", "unit": "Set", "price_range": (85, 125), "qty_range": (1, 100)},
                {"description": "Cherry KC 6000 SLIM Tastatur USB deutsch silber Art.-Nr. 88010", "unit": "Stk.", "price_range": (35, 55), "qty_range": (1, 200)},
                {"description": "Logitech MX Master 3S Wireless Maus Bluetooth USB-C graphit Art.-Nr. 88101", "unit": "Stk.", "price_range": (95, 135), "qty_range": (1, 100)},
                {"description": "Microsoft Surface Arc Mouse Bluetooth hellgrau Art.-Nr. 88105", "unit": "Stk.", "price_range": (65, 95), "qty_range": (1, 100)},
                {"description": "Logitech C920s HD Pro Webcam 1080p mit Abdeckung Art.-Nr. 88201", "unit": "Stk.", "price_range": (65, 95), "qty_range": (1, 100)},
                {"description": "Logitech BRIO 4K Stream Edition Webcam HDR USB-C Art.-Nr. 88205", "unit": "Stk.", "price_range": (185, 265), "qty_range": (1, 50)},
                {"description": "Jabra Speak2 75 UC Bluetooth Speakerphone USB-C Art.-Nr. 88301", "unit": "Stk.", "price_range": (280, 380), "qty_range": (1, 50)},
                {"description": "Poly Studio P15 4K Video Bar USB All-in-One Art.-Nr. 88305", "unit": "Stk.", "price_range": (750, 1050), "qty_range": (1, 20)},
                # Docking Stations
                {"description": "Dell WD22TB4 Thunderbolt 4 Dock 180W Dual 4K USB-C Art.-Nr. 89001", "unit": "Stk.", "price_range": (320, 420), "qty_range": (1, 100)},
                {"description": "Lenovo ThinkPad Universal Thunderbolt 4 Dock 40B00135EU Art.-Nr. 89005", "unit": "Stk.", "price_range": (350, 450), "qty_range": (1, 100)},
                {"description": "HP USB-C Dock G5 100W PD 2x DisplayPort HDMI Art.-Nr. 89010", "unit": "Stk.", "price_range": (250, 350), "qty_range": (1, 100)},
                {"description": "CalDigit TS4 Thunderbolt 4 Dock 18 Ports 98W PD Art.-Nr. 89015", "unit": "Stk.", "price_range": (380, 480), "qty_range": (1, 50)},
                # Services
                {"description": "IT-Arbeitsplatz-Installation vor Ort inkl. Datenmigration Art.-Nr. 90001", "unit": "Stk.", "price_range": (85, 145)},
                {"description": "Server-Installation Rack-Einbau inkl. Verkabelung Art.-Nr. 90005", "unit": "Stk.", "price_range": (280, 450)},
                {"description": "Netzwerk-Konfiguration Switch/Router/Firewall pro Gerät Art.-Nr. 90010", "unit": "Gerät", "price_range": (120, 220)},
                {"description": "WLAN-Ausleuchtung und Site Survey pro 500m² Art.-Nr. 90015", "unit": "Einheit", "price_range": (450, 750)},
                {"description": "Techniker vor Ort IT-Service Stundensatz Art.-Nr. 90101", "unit": "Std.", "price_range": (95, 145)},
                {"description": "Remote-Support IT-Service Stundensatz Art.-Nr. 90105", "unit": "Std.", "price_range": (75, 115)},
            ],
        },
        "T9_INDUSTRIE": {
            "supplier": "IndustrieTechnik Weber KG",
            "supplier_address": "Industriepark 23, 45127 Essen",
            "description": "Industrieausrüstung und Komponenten",
            "position_count_range": (8, 35),
            "positions": [
                # Drucksensoren und -transmitter
                {"description": "Drucktransmitter Endress+Hauser Cerabar PMP71 0-10bar 4-20mA HART Art.-Nr. 91001", "unit": "Stk.", "price_range": (850, 1450), "qty_range": (1, 20)},
                {"description": "Drucksensor WIKA S-20 0-16bar G1/4 Edelstahl 316L Art.-Nr. 91005", "unit": "Stk.", "price_range": (185, 320), "qty_range": (1, 50)},
                {"description": "Differenzdrucktransmitter Siemens SITRANS P DS III 0-1bar Art.-Nr. 91010", "unit": "Stk.", "price_range": (1250, 1950), "qty_range": (1, 10)},
                {"description": "Druckschalter SUCO 0184 1-10bar SPDT M12 Stecker Art.-Nr. 91015", "unit": "Stk.", "price_range": (85, 145), "qty_range": (1, 50)},
                {"description": "Manometer Glycerin 100mm 0-25bar Edelstahl 1/2\" unten Art.-Nr. 91020", "unit": "Stk.", "price_range": (45, 85), "qty_range": (1, 100)},
                {"description": "Druckminderer Festo LR-1/4-D-MINI 0.5-12bar Art.-Nr. 91025", "unit": "Stk.", "price_range": (65, 120), "qty_range": (1, 50)},
                # Temperatursensoren
                {"description": "Temperaturfühler PT100 Klasse A 6x100mm M12 Stecker Art.-Nr. 92001", "unit": "Stk.", "price_range": (85, 165), "qty_range": (1, 50)},
                {"description": "Thermoelement Typ K NiCr-Ni 3x150mm mit Anschlusskopf Form B Art.-Nr. 92005", "unit": "Stk.", "price_range": (65, 125), "qty_range": (1, 50)},
                {"description": "Temperaturtransmitter Endress+Hauser iTEMP TMT82 HART Art.-Nr. 92010", "unit": "Stk.", "price_range": (420, 680), "qty_range": (1, 30)},
                {"description": "Widerstandsthermometer PT1000 Einschraubfühler G1/2 200mm Art.-Nr. 92015", "unit": "Stk.", "price_range": (95, 175), "qty_range": (1, 50)},
                {"description": "Infrarot-Pyrometer Optris CT LT -50 bis 975°C Art.-Nr. 92020", "unit": "Stk.", "price_range": (450, 780), "qty_range": (1, 20)},
                {"description": "Bimetall-Thermometer 100mm 0-120°C 1/2\" axial Art.-Nr. 92025", "unit": "Stk.", "price_range": (28, 55), "qty_range": (1, 100)},
                {"description": "Temperaturregler Eurotherm 3216 PID 1/16 DIN Art.-Nr. 92030", "unit": "Stk.", "price_range": (380, 620), "qty_range": (1, 20)},
                # Durchflusssensoren
                {"description": "Magnetisch-induktiver Durchflussmesser E+H Promag W 400 DN50 Art.-Nr. 93001", "unit": "Stk.", "price_range": (2850, 4250), "qty_range": (1, 10)},
                {"description": "Ultraschall-Durchflussmesser Siemens SITRANS FUP1010 Clamp-on Art.-Nr. 93005", "unit": "Stk.", "price_range": (3850, 5850), "qty_range": (1, 5)},
                {"description": "Coriolis-Massendurchflussmesser E+H Promass F 300 DN25 Art.-Nr. 93010", "unit": "Stk.", "price_range": (6850, 9850), "qty_range": (1, 5)},
                {"description": "Schwebekörper-Durchflussmesser Krohne H250 M40 DN25 Art.-Nr. 93015", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 20)},
                {"description": "Vortex-Durchflussmesser E+H Prowirl F 200 DN50 Art.-Nr. 93020", "unit": "Stk.", "price_range": (2450, 3650), "qty_range": (1, 10)},
                {"description": "Turbinen-Durchflussmesser ifm SM6000 G1\" 0.3-10 l/min Art.-Nr. 93025", "unit": "Stk.", "price_range": (285, 450), "qty_range": (1, 30)},
                # Füllstandssensoren
                {"description": "Radar-Füllstandsmessgerät VEGA VEGAPULS 64 Art.-Nr. 94001", "unit": "Stk.", "price_range": (1850, 2850), "qty_range": (1, 15)},
                {"description": "Kapazitiver Füllstandssensor ifm LK3122 M12 200mm Art.-Nr. 94005", "unit": "Stk.", "price_range": (185, 320), "qty_range": (1, 50)},
                {"description": "Ultraschall-Füllstandssensor E+H Prosonic FMU30 Art.-Nr. 94010", "unit": "Stk.", "price_range": (950, 1550), "qty_range": (1, 20)},
                {"description": "Schwimmerschalter WIKA FLS-S Edelstahl 1000mm Art.-Nr. 94015", "unit": "Stk.", "price_range": (125, 220), "qty_range": (1, 50)},
                {"description": "Vibrations-Grenzstandschalter E+H Liquiphant FTL51 Art.-Nr. 94020", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 20)},
                {"description": "Hydrostatischer Füllstandssensor WIKA LS-10 0-10m Art.-Nr. 94025", "unit": "Stk.", "price_range": (450, 780), "qty_range": (1, 30)},
                # Näherungssensoren und Positionsgeber
                {"description": "Induktiver Näherungsschalter ifm IE5343 M18 8mm PNP NO Art.-Nr. 95001", "unit": "Stk.", "price_range": (45, 85), "qty_range": (5, 100)},
                {"description": "Kapazitiver Näherungsschalter ifm KI5087 M30 15mm PNP NO Art.-Nr. 95005", "unit": "Stk.", "price_range": (85, 145), "qty_range": (2, 50)},
                {"description": "Optischer Sensor Sick WTB4-3P2161 Reflexions-Lichttaster Art.-Nr. 95010", "unit": "Stk.", "price_range": (125, 220), "qty_range": (2, 50)},
                {"description": "Lichtschranke Sick WS/WE160-F440 Einweglichtschranke Art.-Nr. 95015", "unit": "Stk.", "price_range": (185, 320), "qty_range": (2, 30)},
                {"description": "Laser-Distanzsensor Sick DT35-B15251 0.05-12m Art.-Nr. 95020", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 20)},
                {"description": "Magnetischer Zylinderschalter Festo SME-8M-DS-24V-K-2.5-OE Art.-Nr. 95025", "unit": "Stk.", "price_range": (28, 52), "qty_range": (5, 100)},
                {"description": "Absolutwert-Drehgeber Sick AFS60A-S1AM262144 SSI Art.-Nr. 95030", "unit": "Stk.", "price_range": (450, 750), "qty_range": (1, 20)},
                {"description": "Inkremental-Drehgeber Sick DFS60B-S4AA10000 10000 Impulse Art.-Nr. 95035", "unit": "Stk.", "price_range": (285, 480), "qty_range": (1, 30)},
                {"description": "Linearpotentiometer Novotechnik TLH-0150 150mm 10kOhm Art.-Nr. 95040", "unit": "Stk.", "price_range": (185, 320), "qty_range": (1, 30)},
                # Pumpen
                {"description": "Kreiselpumpe Grundfos CRN 3-8 A-FGJ-G-E-HQQE 1,1kW Art.-Nr. 96001", "unit": "Stk.", "price_range": (1850, 2850), "qty_range": (1, 10)},
                {"description": "Tauchpumpe KSB Ama-Porter 501 SE Edelstahl DN50 Art.-Nr. 96005", "unit": "Stk.", "price_range": (1450, 2250), "qty_range": (1, 10)},
                {"description": "Membrandosierpumpe ProMinent gamma/L 1,0 l/h 25bar Art.-Nr. 96010", "unit": "Stk.", "price_range": (850, 1350), "qty_range": (1, 20)},
                {"description": "Schlauchpumpe Watson-Marlow 520Du 0.0004-2200 ml/min Art.-Nr. 96015", "unit": "Stk.", "price_range": (2850, 4250), "qty_range": (1, 5)},
                {"description": "Zahnradpumpe Maag S42 100 cm³/U Edelstahl Art.-Nr. 96020", "unit": "Stk.", "price_range": (3850, 5850), "qty_range": (1, 5)},
                {"description": "Exzenterschneckenpumpe Netzsch NEMO NM 021BY01L06B Art.-Nr. 96025", "unit": "Stk.", "price_range": (2450, 3850), "qty_range": (1, 8)},
                {"description": "Druckluft-Membranpumpe Wilden P200 PPPP Kunststoff Art.-Nr. 96030", "unit": "Stk.", "price_range": (1250, 1950), "qty_range": (1, 15)},
                {"description": "Vakuumpumpe Busch R5 RA 0025 F 25m³/h Art.-Nr. 96035", "unit": "Stk.", "price_range": (2850, 4250), "qty_range": (1, 5)},
                # Rohre
                {"description": "Edelstahlrohr 1.4404 nahtlos Ø 33,7x2,0mm EN 10216-5 Art.-Nr. 97001", "unit": "m", "price_range": (28, 48), "qty_range": (6, 100)},
                {"description": "Edelstahlrohr 1.4571 geschweißt Ø 60,3x2,0mm EN 10217-7 Art.-Nr. 97005", "unit": "m", "price_range": (35, 58), "qty_range": (6, 100)},
                {"description": "Edelstahlrohr 1.4301 Präzisionsrohr Ø 10x1,0mm blank Art.-Nr. 97010", "unit": "m", "price_range": (8, 15), "qty_range": (10, 200)},
                {"description": "PE-HD Druckrohr PE100 SDR11 Ø 63x5,8mm PN16 Art.-Nr. 97101", "unit": "m", "price_range": (8, 15), "qty_range": (10, 200)},
                {"description": "PE-HD Druckrohr PE100 SDR17 Ø 110x6,6mm PN10 Art.-Nr. 97105", "unit": "m", "price_range": (15, 28), "qty_range": (10, 200)},
                {"description": "PVC-U Druckrohr PN16 Ø 50x3,7mm DIN 8062 grau Art.-Nr. 97110", "unit": "m", "price_range": (5, 12), "qty_range": (10, 200)},
                {"description": "PP-H Rohr SDR11 Ø 40x3,7mm PN10 grau Art.-Nr. 97115", "unit": "m", "price_range": (6, 12), "qty_range": (10, 200)},
                {"description": "Kupferrohr Cu-DHP R290 Ø 28x1,5mm EN 12735-1 Art.-Nr. 97201", "unit": "m", "price_range": (18, 32), "qty_range": (5, 100)},
                {"description": "Kupferrohr Cu-DHP R220 Ø 15x1,0mm Ringware 50m Art.-Nr. 97205", "unit": "Ring", "price_range": (350, 550), "qty_range": (1, 10)},
                {"description": "Präzisionsstahlrohr E235 nahtlos Ø 25x2,0mm EN 10305-1 Art.-Nr. 97301", "unit": "m", "price_range": (8, 15), "qty_range": (10, 200)},
                {"description": "Gewindefitting Edelstahl 1.4408 Winkel 90° 1\" IG/AG Art.-Nr. 97401", "unit": "Stk.", "price_range": (18, 35), "qty_range": (10, 100)},
                {"description": "Klemmringverschraubung Edelstahl 1.4404 Ø 12mm Art.-Nr. 97405", "unit": "Stk.", "price_range": (12, 25), "qty_range": (10, 200)},
                {"description": "Flansch DIN 2633 DN50 PN16 Vorschweißflansch 1.4404 Art.-Nr. 97410", "unit": "Stk.", "price_range": (45, 85), "qty_range": (2, 50)},
                {"description": "Schweißbogen 90° Edelstahl 1.4404 Ø 42,4x2,0mm Art.-Nr. 97415", "unit": "Stk.", "price_range": (8, 18), "qty_range": (5, 100)},
                {"description": "T-Stück Edelstahl 1.4404 Ø 33,7x2,0mm geschweißt Art.-Nr. 97420", "unit": "Stk.", "price_range": (12, 25), "qty_range": (5, 100)},
                # Armaturen
                {"description": "Kugelhahn Edelstahl 1.4408 DN40 PN40 Volldurchgang Art.-Nr. 98001", "unit": "Stk.", "price_range": (125, 220), "qty_range": (1, 50)},
                {"description": "Absperrschieber AVK DN100 PN16 Grauguss Flansch Art.-Nr. 98005", "unit": "Stk.", "price_range": (280, 450), "qty_range": (1, 20)},
                {"description": "Rückschlagklappe Wafer DN80 PN16 Edelstahl Art.-Nr. 98010", "unit": "Stk.", "price_range": (185, 320), "qty_range": (1, 30)},
                {"description": "Membranventil GEMÜ 650 DN25 PP/EPDM pneumatisch Art.-Nr. 98015", "unit": "Stk.", "price_range": (450, 750), "qty_range": (1, 20)},
                {"description": "Regelventil Samson Typ 3241 DN25 PN40 Edelstahl Art.-Nr. 98020", "unit": "Stk.", "price_range": (1850, 2850), "qty_range": (1, 10)},
                {"description": "Magnetventil Bürkert 6013 G1/4 24V DC Messing Art.-Nr. 98025", "unit": "Stk.", "price_range": (85, 145), "qty_range": (2, 50)},
                {"description": "Pneumatikzylinder Festo DSBC-50-100-PPVA-N3 Art.-Nr. 98030", "unit": "Stk.", "price_range": (250, 420), "qty_range": (1, 30)},
                # Kabel und Leitungen
                {"description": "Steuerkabel ÖLFLEX CLASSIC 110 4G1,5mm² LAPP 1119304 Art.-Nr. 99001", "unit": "m", "price_range": (2.50, 4.20), "qty_range": (50, 1000)},
                {"description": "Steuerkabel ÖLFLEX CLASSIC 110 CY 7G1,0mm² geschirmt Art.-Nr. 99005", "unit": "m", "price_range": (4.80, 7.50), "qty_range": (50, 500)},
                {"description": "Datenleitung UNITRONIC LiYCY 4x0,34mm² geschirmt Art.-Nr. 99010", "unit": "m", "price_range": (1.80, 3.20), "qty_range": (50, 1000)},
                {"description": "PROFIBUS-Kabel Siemens 6XV1830-0EH10 2x0,64mm² Art.-Nr. 99015", "unit": "m", "price_range": (3.50, 5.80), "qty_range": (50, 500)},
                {"description": "Ethernet-Kabel Industrial Cat.5e SF/UTP 4x2xAWG22 Art.-Nr. 99020", "unit": "m", "price_range": (2.20, 3.80), "qty_range": (50, 500)},
                {"description": "Energiekabel NYY-J 5x10mm² RE 0,6/1kV schwarz Art.-Nr. 99101", "unit": "m", "price_range": (12, 22), "qty_range": (25, 500)},
                {"description": "Energiekabel NYY-J 5x6mm² RE 0,6/1kV schwarz Art.-Nr. 99105", "unit": "m", "price_range": (8, 15), "qty_range": (25, 500)},
                {"description": "Energiekabel NYM-J 5x2,5mm² grau VDE Art.-Nr. 99110", "unit": "m", "price_range": (3.50, 5.80), "qty_range": (50, 500)},
                {"description": "Schleppkettenkabel ÖLFLEX CHAIN 809 4G1,0mm² Art.-Nr. 99201", "unit": "m", "price_range": (4.20, 6.80), "qty_range": (25, 300)},
                {"description": "Servokabel ÖLFLEX SERVO 2YSLCY-JB 4G4+2x1,0mm² Art.-Nr. 99205", "unit": "m", "price_range": (12, 22), "qty_range": (25, 200)},
                {"description": "M12 Sensorleitung gerade 4-polig PNP 5m Murrelektronik Art.-Nr. 99301", "unit": "Stk.", "price_range": (12, 22), "qty_range": (10, 200)},
                {"description": "M12 Sensorleitung gewinkelt 4-polig 2m ifm EVC001 Art.-Nr. 99305", "unit": "Stk.", "price_range": (15, 28), "qty_range": (10, 200)},
                {"description": "M12 Y-Verteiler 4-polig 2x Buchse 1x Stecker Art.-Nr. 99310", "unit": "Stk.", "price_range": (25, 45), "qty_range": (5, 100)},
                # Schaltschranktechnik
                {"description": "Schaltschrank AE Rittal 1060.500 600x600x210mm IP66 Art.-Nr. 100001", "unit": "Stk.", "price_range": (280, 450), "qty_range": (1, 20)},
                {"description": "Schaltschrank AE Rittal 1380.500 800x1200x300mm IP66 Art.-Nr. 100005", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 10)},
                {"description": "Montageplatte verzinkt 565x365mm für AE 1060 Art.-Nr. 100010", "unit": "Stk.", "price_range": (35, 65), "qty_range": (1, 30)},
                {"description": "Tragschiene TS35x7,5mm gelocht 2m EN 60715 Art.-Nr. 100015", "unit": "Stk.", "price_range": (8, 15), "qty_range": (5, 50)},
                {"description": "Kabelkanal Betaduct 50x50mm 2m grau mit Deckel Art.-Nr. 100020", "unit": "Stk.", "price_range": (12, 22), "qty_range": (5, 100)},
                {"description": "Reihenklemme Phoenix DIKD 1,5 Durchgangsklemme 0,14-1,5mm² Art.-Nr. 100101", "unit": "Stk.", "price_range": (0.85, 1.45), "qty_range": (50, 500)},
                {"description": "Reihenklemme Phoenix PT 2,5 Push-in 0,14-4mm² Art.-Nr. 100105", "unit": "Stk.", "price_range": (1.20, 2.10), "qty_range": (50, 500)},
                {"description": "Sicherungsklemme Phoenix UK 5-HESI G 5x20mm Art.-Nr. 100110", "unit": "Stk.", "price_range": (4.50, 7.80), "qty_range": (10, 100)},
                {"description": "Potentialverteiler Phoenix PTFIX 6/18x2,5-NS35 Art.-Nr. 100115", "unit": "Stk.", "price_range": (18, 32), "qty_range": (5, 50)},
                # SPS und Automatisierung
                {"description": "CPU Siemens S7-1500 6ES7511-1AK02-0AB0 CPU 1511-1 PN Art.-Nr. 101001", "unit": "Stk.", "price_range": (1250, 1850), "qty_range": (1, 10)},
                {"description": "CPU Siemens S7-1200 6ES7214-1AG40-0XB0 CPU 1214C DC/DC/DC Art.-Nr. 101005", "unit": "Stk.", "price_range": (350, 520), "qty_range": (1, 20)},
                {"description": "Digital-Eingabe SM 1221 8xDI 24V DC Sink/Source Art.-Nr. 101101", "unit": "Stk.", "price_range": (120, 195), "qty_range": (1, 30)},
                {"description": "Digital-Ausgabe SM 1222 8xDO 24V DC 0,5A Art.-Nr. 101105", "unit": "Stk.", "price_range": (145, 235), "qty_range": (1, 30)},
                {"description": "Analog-Eingabe SM 1231 4xAI +/-10V 13Bit Art.-Nr. 101110", "unit": "Stk.", "price_range": (280, 420), "qty_range": (1, 20)},
                {"description": "Analog-Ausgabe SM 1232 4xAO +/-10V 14Bit Art.-Nr. 101115", "unit": "Stk.", "price_range": (320, 480), "qty_range": (1, 20)},
                {"description": "PROFINET-Switch CSM 1277 4-Port unmanaged Art.-Nr. 101201", "unit": "Stk.", "price_range": (185, 295), "qty_range": (1, 20)},
                # Antriebstechnik
                {"description": "Frequenzumrichter Siemens SINAMICS G120C 7,5kW 380-480V Art.-Nr. 102001", "unit": "Stk.", "price_range": (850, 1350), "qty_range": (1, 15)},
                {"description": "Frequenzumrichter Danfoss VLT FC-302 11kW 3x380-480V Art.-Nr. 102005", "unit": "Stk.", "price_range": (1450, 2250), "qty_range": (1, 10)},
                {"description": "Servoregler Siemens SINAMICS S120 PM340 3kW Art.-Nr. 102010", "unit": "Stk.", "price_range": (1850, 2850), "qty_range": (1, 10)},
                {"description": "Servomotor Siemens 1FK7044-2AK71 2,2Nm 3000rpm Art.-Nr. 102101", "unit": "Stk.", "price_range": (1250, 1950), "qty_range": (1, 15)},
                {"description": "Drehstrommotor IE3 SEW DRN80M4 0,75kW 1400rpm B14 Art.-Nr. 102105", "unit": "Stk.", "price_range": (320, 520), "qty_range": (1, 30)},
                {"description": "Drehstrommotor IE3 Siemens 1LE1003 4,0kW 1500rpm B3 Art.-Nr. 102110", "unit": "Stk.", "price_range": (580, 920), "qty_range": (1, 20)},
                {"description": "Getriebemotor SEW R47 DRN80M4 0,75kW i=20,62 Art.-Nr. 102201", "unit": "Stk.", "price_range": (650, 1050), "qty_range": (1, 15)},
                {"description": "Stirnradgetriebe Flender SIG 20 A i=10 Hohlwelle Art.-Nr. 102205", "unit": "Stk.", "price_range": (450, 750), "qty_range": (1, 20)},
                # Schutzgeräte
                {"description": "Leistungsschalter Siemens 3VA1140-4ED36-0AA0 40A 3p Art.-Nr. 103001", "unit": "Stk.", "price_range": (185, 320), "qty_range": (1, 30)},
                {"description": "Motorschutzschalter Siemens 3RV2011-1JA10 7-10A Art.-Nr. 103005", "unit": "Stk.", "price_range": (65, 115), "qty_range": (1, 50)},
                {"description": "Schütz Siemens 3RT2026-1BB40 24V DC 25A AC-3 Art.-Nr. 103010", "unit": "Stk.", "price_range": (85, 145), "qty_range": (1, 50)},
                {"description": "Hilfsschütz Siemens 3RH2131-1BB40 24V DC 3S+1Ö Art.-Nr. 103015", "unit": "Stk.", "price_range": (45, 78), "qty_range": (2, 50)},
                {"description": "Überspannungsableiter Phoenix VAL-SEC-T2-3S-350 Art.-Nr. 103020", "unit": "Stk.", "price_range": (120, 195), "qty_range": (1, 30)},
                {"description": "Netzteil Phoenix QUINT4-PS/1AC/24DC/10 10A Art.-Nr. 103101", "unit": "Stk.", "price_range": (280, 450), "qty_range": (1, 20)},
                {"description": "Netzteil Siemens SITOP PSU8200 24V/20A Art.-Nr. 103105", "unit": "Stk.", "price_range": (380, 580), "qty_range": (1, 15)},
                # Dienstleistungen
                {"description": "Inbetriebnahme SPS-Steuerung inkl. Dokumentation Art.-Nr. 104001", "unit": "Tag", "price_range": (850, 1250)},
                {"description": "Inbetriebnahme Frequenzumrichter inkl. Parametrierung Art.-Nr. 104005", "unit": "Stk.", "price_range": (185, 320)},
                {"description": "Schaltschrankbau nach Zeichnung pro Einheit Art.-Nr. 104010", "unit": "Stk.", "price_range": (650, 1250)},
                {"description": "Elektromontage vor Ort Industrieanlagen Art.-Nr. 104101", "unit": "Std.", "price_range": (65, 95)},
                {"description": "Rohrleitungsmontage Edelstahl inkl. WIG-Schweißen Art.-Nr. 104105", "unit": "Std.", "price_range": (75, 115)},
                {"description": "SPS-Programmierung TIA Portal pro Std. Art.-Nr. 104110", "unit": "Std.", "price_range": (95, 145)},
                {"description": "Mess- und Regeltechnik Inbetriebnahme Art.-Nr. 104115", "unit": "Std.", "price_range": (85, 125)},
            ],
        },
    }

    config = templates_config.get(template, templates_config["T1_HANDWERK"])

    # Positionen generieren
    position_count = random.randint(*config.get("position_count_range", (3, 8)))
    available_positions = config["positions"]
    selected_positions = random.sample(
        available_positions,
        min(position_count, len(available_positions))
    )

    positions: list[dict[str, Any]] = []
    net_amount = 0.0

    for i, pos_template in enumerate(selected_positions, start=1):
        qty_range = pos_template.get("qty_range", (1, 10))
        quantity = random.randint(*qty_range) if qty_range[1] > 1 else qty_range[0]
        # Für kleine Einheiten (Wort, etc.) höhere Mengen
        if pos_template["unit"] in ["Wort", "Seite", "Bild"]:
            quantity = random.randint(50, 500)
        elif pos_template["unit"] in ["m"]:
            quantity = round(random.uniform(2, 25), 1)

        unit_price = round(random.uniform(*pos_template["price_range"]), 2)
        line_total = round(quantity * unit_price, 2)
        net_amount += line_total

        positions.append({
            "pos": i,
            "description": pos_template["description"],
            "quantity": quantity,
            "unit": pos_template["unit"],
            "unit_price": unit_price,
            "total": line_total,
        })

    net_amount = round(net_amount, 2)
    vat_rate = 19 if net_amount > 50 else 7
    vat_amount = round(net_amount * vat_rate / 100, 2)
    gross_amount = round(net_amount + vat_amount, 2)

    # Empfängerdaten aus Begünstigtendaten oder Standard (mit Alias-Noise)
    customer_name, customer_address = _resolve_customer_data(
        beneficiary_data, alias_noise_probability
    )

    # Leistungsbeschreibung ggf. mit Projektbezug
    description = _build_description(config["description"], project_context)

    # USt-IdNr generieren (plausibel)
    vat_id = _generate_vat_id(beneficiary_data)

    supply_date = invoice_date - timedelta(days=random.randint(1, 14))

    data = {
        "invoice_number": f"{today.year}-{index:04d}",
        "invoice_date": invoice_date.strftime(date_format_python),
        "supplier_name": config["supplier"],
        "supplier_address": config["supplier_address"],
        "vat_id": vat_id,
        "customer_name": customer_name,
        "customer_address": customer_address,
        "description": description,
        "supply_date": supply_date.strftime(date_format_python),
        "net_amount": f"{net_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "vat_rate": vat_rate,
        "vat_amount": f"{vat_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "gross_amount": f"{gross_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "iban": f"DE{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(10, 99)}",
        "template": template,
        "positions": positions,  # Positionsliste für Positionstabelle
        "injected_errors": [],
        "correct_values": {},
        # Metadaten für Lösungsdatei
        "beneficiary_used": beneficiary_data is not None,
        "project_id": project_context.get("project_id") if project_context else None,
    }

    # Fehler injizieren (mit Feature-spezifischen Raten)
    if has_error:
        data = _inject_errors(
            data, severity, beneficiary_data, per_feature_error_rates or {}
        )

    return data


def _convert_date_format(format_str: str) -> str:
    """
    Konvertiert Datumsformat-Strings zu Python strftime-Format.

    Args:
        format_str: Format wie "DD.MM.YYYY" oder "YYYY-MM-DD"

    Returns:
        Python strftime Format
    """
    conversions = {
        "DD.MM.YYYY": "%d.%m.%Y",
        "DD/MM/YYYY": "%d/%m/%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "YYYY-MM-DD": "%Y-%m-%d",
        "DD-MM-YYYY": "%d-%m-%Y",
        "D.M.YYYY": "%-d.%-m.%Y",
        "DD. MMMM YYYY": "%d. %B %Y",
    }
    return conversions.get(format_str, "%d.%m.%Y")


def _resolve_customer_data(
    beneficiary_data: dict[str, Any] | None,
    alias_noise_probability: float = 10.0,
) -> tuple[str, str]:
    """
    Ermittelt Empfängername und -adresse aus Begünstigtendaten.

    Args:
        beneficiary_data: Begünstigtendaten oder None
        alias_noise_probability: Wahrscheinlichkeit (%), einen Alias zu verwenden

    Returns:
        Tuple (customer_name, customer_address)
    """
    if not beneficiary_data:
        return "FlowAudit Testprojekt GmbH", "Prüfstraße 1, 10117 Berlin"

    # Name aus Begünstigtendaten (ggf. mit Rechtsform)
    name = beneficiary_data.get("beneficiary_name", "")
    legal_form = beneficiary_data.get("legal_form", "")

    # Alias-Noise: Mit gewisser Wahrscheinlichkeit Alias verwenden
    aliases = beneficiary_data.get("aliases", [])
    if aliases and random.random() * 100 < alias_noise_probability:
        name = random.choice(aliases)
        legal_form = ""  # Bei Alias keine Rechtsform hinzufügen

    if legal_form and legal_form not in name:
        customer_name = f"{name} {legal_form}"
    else:
        customer_name = name

    # Adresse zusammenbauen
    street = beneficiary_data.get("street", "")
    zip_code = beneficiary_data.get("zip", "")
    city = beneficiary_data.get("city", "")

    customer_address = f"{street}, {zip_code} {city}".strip(", ")

    return customer_name, customer_address


def _build_description(
    base_description: str,
    project_context: dict[str, Any] | None,
) -> str:
    """
    Erstellt Leistungsbeschreibung, optional mit Projektbezug.

    Args:
        base_description: Basis-Beschreibung aus Template
        project_context: Projektkontext oder None
            Unterstützte Felder: project_name, project_number, execution_location

    Returns:
        Leistungsbeschreibung
    """
    if not project_context:
        return base_description

    parts = [base_description]
    context_parts = []

    # Projektnummer
    project_number = project_context.get("project_number", "")
    if project_number:
        context_parts.append(f"Projekt-Nr. {project_number}")

    # Projektname
    project_name = project_context.get("project_name", "")
    if project_name:
        context_parts.append(f"Projekt: {project_name}")

    # Durchführungsort
    execution_location = project_context.get("execution_location", "")
    if execution_location:
        context_parts.append(f"Ort: {execution_location}")

    if context_parts:
        parts.append(f"({', '.join(context_parts)})")

    return " ".join(parts)


def _generate_vat_id(beneficiary_data: dict[str, Any] | None) -> str:
    """
    Generiert eine plausible USt-IdNr.

    Args:
        beneficiary_data: Begünstigtendaten (optional, für Ländercode)

    Returns:
        USt-IdNr im korrekten Format
    """
    country = "DE"
    if beneficiary_data:
        country = beneficiary_data.get("country", "DE")

    if country == "DE":
        # Deutsche USt-IdNr: DE + 9 Ziffern
        return f"DE{random.randint(100000000, 999999999)}"
    elif country == "AT":
        # Österreichische USt-IdNr: ATU + 8 Ziffern
        return f"ATU{random.randint(10000000, 99999999)}"
    elif country == "GB":
        # UK VAT: GB + 9 oder 12 Ziffern
        return f"GB{random.randint(100000000, 999999999)}"
    else:
        # EU-Standard: 2 Buchstaben + Ziffern
        return f"{country}{random.randint(100000000, 999999999)}"


def _inject_errors(
    data: dict[str, Any],
    severity: int,
    beneficiary_data: dict[str, Any] | None = None,
    per_feature_error_rates: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Injiziert Fehler in Rechnungsdaten.

    Args:
        data: Rechnungsdaten
        severity: Schweregrad (1-5, bestimmt Anzahl der Fehler)
        beneficiary_data: Begünstigtendaten (für spezifische Fehlertypen)
        per_feature_error_rates: Feature-spezifische Fehlerraten (z.B. {"invoice_number": 30.0})

    Returns:
        Modifizierte Rechnungsdaten mit injizierten Fehlern
    """
    feature_rates = per_feature_error_rates or {}

    # Basis-Fehlertypen (immer verfügbar)
    error_types: list[tuple[str, Any]] = [
        ("missing_invoice_number", lambda d: d.update({
            "invoice_number": "",
            "correct_values": {**d.get("correct_values", {}), "invoice_number": d["invoice_number"]}
        })),
        ("invalid_vat_id", lambda d: d.update({
            "vat_id": "INVALID123",
            "correct_values": {**d.get("correct_values", {}), "vat_id": d["vat_id"]}
        })),
        ("missing_date", lambda d: d.update({
            "invoice_date": "",
            "correct_values": {**d.get("correct_values", {}), "invoice_date": d["invoice_date"]}
        })),
        ("calculation_error", lambda d: d.update({
            "gross_amount": str(float(d["gross_amount"].replace(".", "").replace(",", ".")) + 10).replace(".", ","),
            "correct_values": {**d.get("correct_values", {}), "gross_amount": d["gross_amount"]}
        })),
        ("missing_description", lambda d: d.update({
            "description": "",
            "correct_values": {**d.get("correct_values", {}), "description": d["description"]}
        })),
        ("vat_id_missing", lambda d: d.update({
            "vat_id": "",
            "correct_values": {**d.get("correct_values", {}), "vat_id": d["vat_id"]}
        })),
    ]

    # Begünstigten-spezifische Fehler (nur wenn beneficiary_data vorhanden)
    if beneficiary_data:
        correct_name = data["customer_name"]
        correct_address = data["customer_address"]

        # Tippfehler im Empfängernamen (leicht)
        error_types.append((
            "beneficiary_name_typo",
            lambda d: d.update({
                "customer_name": _add_typo(d["customer_name"]),
                "correct_values": {**d.get("correct_values", {}), "customer_name": correct_name}
            })
        ))

        # Alias statt Hauptname verwenden (leicht)
        aliases = beneficiary_data.get("aliases", [])
        if aliases:
            error_types.append((
                "beneficiary_alias_used",
                lambda d: d.update({
                    "customer_name": random.choice(aliases),
                    "correct_values": {**d.get("correct_values", {}), "customer_name": correct_name}
                })
            ))

        # Falsche Adresse (mittel)
        error_types.append((
            "beneficiary_wrong_address",
            lambda d: d.update({
                "customer_address": "Musterweg 99, 00000 Nirgendwo",
                "correct_values": {**d.get("correct_values", {}), "customer_address": correct_address}
            })
        ))

        # Komplett falscher Empfänger (schwer)
        error_types.append((
            "beneficiary_completely_wrong",
            lambda d: d.update({
                "customer_name": "Unbekannte Firma GmbH",
                "customer_address": "Falschstraße 1, 99999 Anderswo",
                "correct_values": {
                    **d.get("correct_values", {}),
                    "customer_name": correct_name,
                    "customer_address": correct_address
                }
            })
        ))

    # Fehler basierend auf Feature-spezifischen Raten oder Severity auswählen
    selected_errors: list[tuple[str, Any]] = []

    if feature_rates:
        # Feature-spezifische Auswahl: Jeder Fehler hat eigene Rate
        for error_name, error_func in error_types:
            # Mapping von Fehlernamen auf Feature-Keys
            feature_key_map = {
                "missing_invoice_number": "invoice_number",
                "invalid_vat_id": "vat_id",
                "missing_date": "invoice_date",
                "calculation_error": "gross_amount",
                "missing_description": "description",
                "vat_id_missing": "vat_id",
                "beneficiary_name_typo": "beneficiary_name",
                "beneficiary_alias_used": "beneficiary_alias",
                "beneficiary_wrong_address": "beneficiary_address",
                "beneficiary_completely_wrong": "beneficiary",
            }
            feature_key = feature_key_map.get(error_name, error_name)
            rate = feature_rates.get(feature_key, 0.0)

            if random.random() * 100 < rate:
                selected_errors.append((error_name, error_func))
    else:
        # Fallback: Anzahl der Fehler basierend auf Severity
        num_errors = min(severity, len(error_types))
        selected_errors = random.sample(error_types, num_errors)

    for error_name, error_func in selected_errors:
        error_func(data)
        data["injected_errors"].append(error_name)

    return data


def _add_typo(text: str) -> str:
    """Fügt einen realistischen Tippfehler ein."""
    if len(text) < 3:
        return text

    # Verschiedene Typo-Arten
    typo_type = random.choice(["swap", "duplicate", "omit", "replace"])

    chars = list(text)
    pos = random.randint(1, len(chars) - 2)

    if typo_type == "swap" and pos < len(chars) - 1:
        # Buchstaben vertauschen
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    elif typo_type == "duplicate":
        # Buchstaben doppeln
        chars.insert(pos, chars[pos])
    elif typo_type == "omit":
        # Buchstaben auslassen
        chars.pop(pos)
    elif typo_type == "replace":
        # Ähnlichen Buchstaben ersetzen
        similar = {"a": "e", "e": "a", "i": "l", "o": "0", "s": "z", "n": "m"}
        if chars[pos].lower() in similar:
            chars[pos] = similar[chars[pos].lower()]

    return "".join(chars)


def _generate_random_filename(data: dict[str, Any], index: int) -> str:
    """
    Generiert einen zufälligen Dateinamen für eine Rechnung.

    Erzeugt verschiedene realistische Dateinamen-Muster:
    - 2025-12-19_Rechnung_001.pdf
    - Rechnung_MeisterMueller_2025-0001.pdf
    - RE_2025_0001.pdf
    - Invoice_20251219.pdf
    - Lieferantenrechnung_001.pdf
    - RG2025-0001_Handwerk.pdf

    Args:
        data: Rechnungsdaten mit Lieferantenname, Datum, Nummer
        index: Laufende Nummer

    Returns:
        Zufälliger Dateiname (ohne Pfad)
    """
    import re

    # Daten extrahieren
    invoice_date = data.get("invoice_date", "")
    invoice_number = data.get("invoice_number", f"2025-{index:04d}")
    supplier_name = data.get("supplier_name", "Lieferant")
    template = data.get("template", "")

    # Lieferantennamen bereinigen (nur alphanumerisch)
    clean_supplier = re.sub(r"[^a-zA-ZäöüÄÖÜß0-9]", "", supplier_name)[:20]

    # Datum in verschiedenen Formaten
    date_iso = ""
    date_compact = ""
    if invoice_date:
        # Versuche Datum zu parsen (Format: DD.MM.YYYY oder YYYY-MM-DD)
        try:
            if "." in invoice_date:
                parts = invoice_date.split(".")
                if len(parts) == 3:
                    date_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    date_compact = f"{parts[2]}{parts[1]}{parts[0]}"
            elif "-" in invoice_date:
                date_iso = invoice_date
                date_compact = invoice_date.replace("-", "")
        except Exception:
            date_iso = datetime.now().strftime("%Y-%m-%d")
            date_compact = datetime.now().strftime("%Y%m%d")
    else:
        date_iso = datetime.now().strftime("%Y-%m-%d")
        date_compact = datetime.now().strftime("%Y%m%d")

    # Verschiedene Dateinamen-Muster
    patterns = [
        f"{date_iso}_Rechnung_{index:03d}.pdf",
        f"Rechnung_{clean_supplier}_{invoice_number}.pdf",
        f"RE_{invoice_number.replace('-', '_')}.pdf",
        f"Invoice_{date_compact}.pdf",
        f"Lieferantenrechnung_{index:03d}.pdf",
        f"RG{invoice_number}_{template.split('_')[-1] if '_' in template else template}.pdf",
        f"Rechnung-{index:04d}.pdf",
        f"{date_compact}_RE{index:03d}.pdf",
        f"INV-{invoice_number}.pdf",
        f"Rg_{clean_supplier[:10]}_{date_compact}.pdf",
        f"{invoice_number}_Rechnung.pdf",
        f"Bill_{date_iso}_{index:02d}.pdf",
    ]

    return random.choice(patterns)


def _create_error_overview(solutions: list[dict[str, Any]], ruleset_id: str) -> str:
    """
    Erstellt eine Fehler-Übersichtsdatei für Trainer.

    Args:
        solutions: Liste der Lösungsdaten pro Rechnung
        ruleset_id: Aktives Regelwerk

    Returns:
        Formatierter Text mit Fehlerübersicht
    """
    # Regelwerk-spezifische Fehlerbeschreibungen
    error_descriptions = {
        "DE_USTG": {
            "missing_invoice_number": "Rechnungsnummer fehlt (§14 Abs. 4 Nr. 1 UStG)",
            "invalid_vat_id": "Ungültige USt-IdNr. (§14 Abs. 4 Nr. 2 UStG)",
            "missing_date": "Rechnungsdatum fehlt (§14 Abs. 4 Nr. 3 UStG)",
            "calculation_error": "Rechenfehler bei Beträgen (§14 Abs. 4 Nr. 7-8 UStG)",
            "missing_description": "Leistungsbeschreibung fehlt (§14 Abs. 4 Nr. 5 UStG)",
            "vat_id_missing": "USt-IdNr. fehlt komplett (§14 Abs. 4 Nr. 2 UStG)",
            "beneficiary_name_typo": "Tippfehler im Empfängernamen (§14 Abs. 4 Nr. 1 UStG)",
            "beneficiary_alias_used": "Alias statt offiziellem Namen verwendet",
            "beneficiary_wrong_address": "Falsche Empfängeradresse (§14 Abs. 4 Nr. 1 UStG)",
            "beneficiary_completely_wrong": "Falscher Rechnungsempfänger (§14 Abs. 4 Nr. 1 UStG)",
        },
        "EU_VAT": {
            "missing_invoice_number": "Invoice number missing (Art. 226(2) VAT Directive)",
            "invalid_vat_id": "Invalid VAT ID (Art. 226(3) VAT Directive)",
            "missing_date": "Invoice date missing (Art. 226(1) VAT Directive)",
            "calculation_error": "Calculation error (Art. 226(8-10) VAT Directive)",
            "missing_description": "Service description missing (Art. 226(6) VAT Directive)",
            "vat_id_missing": "VAT ID missing (Art. 226(3) VAT Directive)",
            "beneficiary_name_typo": "Typo in recipient name",
            "beneficiary_alias_used": "Alias used instead of official name",
            "beneficiary_wrong_address": "Wrong recipient address (Art. 226(5) VAT Directive)",
            "beneficiary_completely_wrong": "Wrong recipient (Art. 226(5) VAT Directive)",
        },
        "CH_MWSTG": {
            "missing_invoice_number": "Rechnungsnummer fehlt (Art. 26 Abs. 2 MWSTG)",
            "invalid_vat_id": "Ungültige MWST-Nr. (Art. 26 Abs. 2 MWSTG)",
            "missing_date": "Rechnungsdatum fehlt (Art. 26 Abs. 2 MWSTG)",
            "calculation_error": "Rechenfehler (Art. 26 Abs. 2 MWSTG)",
            "missing_description": "Leistungsbeschreibung fehlt (Art. 26 Abs. 2 MWSTG)",
            "vat_id_missing": "MWST-Nr. fehlt (Art. 26 Abs. 2 MWSTG)",
            "beneficiary_name_typo": "Tippfehler im Empfängernamen",
            "beneficiary_alias_used": "Alias statt offizieller Name",
            "beneficiary_wrong_address": "Falsche Empfängeradresse",
            "beneficiary_completely_wrong": "Falscher Rechnungsempfänger",
        },
    }

    # Fallback auf DE_USTG wenn Regelwerk nicht gefunden
    descriptions = error_descriptions.get(ruleset_id, error_descriptions["DE_USTG"])

    lines = [
        "=" * 80,
        "FEHLERÜBERSICHT - RECHNUNGSPRÜFUNG",
        f"Regelwerk: {ruleset_id}",
        "=" * 80,
        "",
        f"Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"Anzahl Rechnungen: {len(solutions)}",
        f"Rechnungen mit Fehlern: {sum(1 for s in solutions if s.get('has_error'))}",
        "",
        "-" * 80,
        "",
    ]

    # Rechnungen mit Fehlern auflisten
    invoices_with_errors = [s for s in solutions if s.get("has_error") and s.get("errors")]
    invoices_without_errors = [s for s in solutions if not s.get("has_error") or not s.get("errors")]

    if invoices_with_errors:
        lines.append("RECHNUNGEN MIT FEHLERN:")
        lines.append("-" * 40)
        lines.append("")

        for solution in invoices_with_errors:
            filename = solution.get("filename", "unbekannt")
            errors = solution.get("errors", [])
            correct_values = solution.get("correct_values", {})

            lines.append(f"📄 {filename}")
            lines.append(f"   Template: {solution.get('template', 'unbekannt')}")
            lines.append(f"   Anzahl Fehler: {len(errors)}")
            lines.append("")

            for error in errors:
                error_desc = descriptions.get(error, error)
                lines.append(f"   ❌ {error_desc}")

                # Korrekten Wert anzeigen wenn verfügbar
                if error in ["missing_invoice_number", "missing_date", "missing_description"]:
                    field_map = {
                        "missing_invoice_number": "invoice_number",
                        "missing_date": "invoice_date",
                        "missing_description": "description",
                    }
                    field = field_map.get(error, "")
                    if field and field in correct_values:
                        lines.append(f"      → Korrekter Wert: {correct_values[field]}")

                if error == "invalid_vat_id" and "vat_id" in correct_values:
                    lines.append(f"      → Korrekte USt-IdNr.: {correct_values['vat_id']}")

                if error == "calculation_error" and "gross_amount" in correct_values:
                    lines.append(f"      → Korrekter Bruttobetrag: {correct_values['gross_amount']}")

                if error in ["beneficiary_name_typo", "beneficiary_alias_used", "beneficiary_completely_wrong"]:
                    if "customer_name" in correct_values:
                        lines.append(f"      → Korrekter Name: {correct_values['customer_name']}")

                if error in ["beneficiary_wrong_address", "beneficiary_completely_wrong"]:
                    if "customer_address" in correct_values:
                        lines.append(f"      → Korrekte Adresse: {correct_values['customer_address']}")

            lines.append("")

    if invoices_without_errors:
        lines.append("")
        lines.append("FEHLERFREIE RECHNUNGEN:")
        lines.append("-" * 40)
        for solution in invoices_without_errors:
            lines.append(f"   ✓ {solution.get('filename', 'unbekannt')}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("ENDE DER FEHLERÜBERSICHT")
    lines.append("=" * 80)

    return "\n".join(lines)


def _format_invoice_pdf(data: dict[str, Any], filepath: Path) -> None:
    """
    Erstellt eine professionelle PDF-Rechnung.

    Args:
        data: Rechnungsdaten
        filepath: Ausgabepfad für die PDF
    """
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles definieren
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=24,
        alignment=1,  # Center
        spaceAfter=20,
        textColor=colors.darkblue,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.darkblue,
        spaceBefore=15,
        spaceAfter=8,
        borderWidth=0,
        borderColor=colors.darkblue,
        borderPadding=5,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )
    bold_style = ParagraphStyle(
        "Bold",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        fontName="Helvetica-Bold",
    )

    elements = []

    # Titel
    elements.append(Paragraph("RECHNUNG", title_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Rechnungsinformationen
    invoice_info = [
        ["Rechnungsnummer:", data.get("invoice_number", "")],
        ["Rechnungsdatum:", data.get("invoice_date", "")],
    ]
    info_table = Table(invoice_info, colWidths=[4 * cm, 8 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.8 * cm))

    # Rechnungssteller
    elements.append(Paragraph("RECHNUNGSSTELLER", heading_style))
    supplier_text = f"""
    <b>{data.get('supplier_name', '')}</b><br/>
    {data.get('supplier_address', '')}<br/>
    USt-IdNr.: {data.get('vat_id', '')}
    """
    elements.append(Paragraph(supplier_text, normal_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Rechnungsempfänger
    elements.append(Paragraph("RECHNUNGSEMPFÄNGER", heading_style))
    customer_text = f"""
    <b>{data.get('customer_name', '')}</b><br/>
    {data.get('customer_address', '')}
    """
    elements.append(Paragraph(customer_text, normal_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Leistung
    elements.append(Paragraph("LEISTUNG", heading_style))
    service_text = f"""
    Leistungsdatum: {data.get('supply_date', '')}<br/><br/>
    {data.get('description', '')}
    """
    elements.append(Paragraph(service_text, normal_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Positionstabelle
    positions = data.get("positions", [])
    if positions:
        elements.append(Paragraph("POSITIONEN", heading_style))

        # Tabellenkopf
        pos_header = ["Pos", "Beschreibung", "Menge", "Einheit", "Einzelpreis", "Betrag"]
        pos_data = [pos_header]

        # Positionen einfügen
        for pos in positions:
            quantity = pos.get("quantity", 0)
            # Formatierung: Ganzzahlen ohne Dezimalstellen, sonst mit
            if isinstance(quantity, float) and quantity == int(quantity):
                qty_str = str(int(quantity))
            elif isinstance(quantity, float):
                qty_str = f"{quantity:.1f}".replace(".", ",")
            else:
                qty_str = str(quantity)

            unit_price = pos.get("unit_price", 0)
            total = pos.get("total", 0)

            pos_data.append([
                str(pos.get("pos", "")),
                pos.get("description", ""),
                qty_str,
                pos.get("unit", ""),
                f"{unit_price:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
            ])

        # Spaltenbreiten: Pos(1cm), Beschreibung(6cm), Menge(1.5cm), Einheit(1.5cm), Einzelpreis(2.5cm), Betrag(2.5cm)
        pos_table = Table(pos_data, colWidths=[1 * cm, 6 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm])
        pos_table.setStyle(TableStyle([
            # Header-Styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Daten-Styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Pos zentriert
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),   # Menge rechts
            ("ALIGN", (4, 1), (-1, -1), "RIGHT"),  # Preise rechts
            ("VALIGN", (0, 1), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            # Zebrastreifen
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            # Rahmen
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOX", (0, 0), (-1, -1), 1, colors.darkblue),
        ]))
        elements.append(pos_table)
        elements.append(Spacer(1, 0.8 * cm))
    else:
        elements.append(Spacer(1, 0.3 * cm))

    # Beträge-Tabelle
    elements.append(Paragraph("BETRÄGE", heading_style))
    amounts_data = [
        ["Nettobetrag:", f"{data.get('net_amount', '')} EUR"],
        [f"MwSt. {data.get('vat_rate', '')}%:", f"{data.get('vat_amount', '')} EUR"],
        ["Bruttobetrag:", f"{data.get('gross_amount', '')} EUR"],
    ]
    amounts_table = Table(amounts_data, colWidths=[8 * cm, 4 * cm])
    amounts_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
        ("LINEBELOW", (0, 2), (-1, 2), 2, colors.black),
        ("BACKGROUND", (0, 2), (-1, 2), colors.lightgrey),
    ]))
    elements.append(amounts_table)
    elements.append(Spacer(1, 1 * cm))

    # Zahlungsinformationen
    elements.append(Paragraph("ZAHLUNGSINFORMATIONEN", heading_style))
    payment_text = f"""
    Zahlbar innerhalb von 14 Tagen.<br/><br/>
    <b>Bankverbindung:</b><br/>
    IBAN: {data.get('iban', '')}
    """
    elements.append(Paragraph(payment_text, normal_style))

    # PDF erstellen
    doc.build(elements)


# =============================================================================
# Export Task
# =============================================================================


@celery_app.task(bind=True, max_retries=2)
def export_results_task(
    self,
    export_job_id: str,
) -> dict[str, Any]:
    """
    Exportiert Analyseergebnisse.

    Args:
        export_job_id: Export-Job-ID

    Returns:
        Dict mit Export-Ergebnis
    """
    logger.info(f"Exporting results for job: {export_job_id}")

    try:
        result = run_async(_export_results_async(export_job_id))
        return result

    except Exception as e:
        logger.exception(f"Error exporting results: {e}")
        self.retry(exc=e, countdown=60)


async def _export_results_async(export_job_id: str) -> dict[str, Any]:
    """Async-Implementation des Exports."""
    celery_session_maker = get_celery_session_maker()
    async with celery_session_maker() as session:
        # Job laden
        export_job = await session.get(ExportJob, export_job_id)
        if not export_job:
            raise ValueError(f"Export job not found: {export_job_id}")

        export_job.status = "RUNNING"
        await session.commit()

        try:
            # Dokumente für Export sammeln
            query = select(Document)

            if export_job.project_id:
                query = query.where(Document.project_id == export_job.project_id)

            if export_job.document_ids:
                query = query.where(Document.id.in_(export_job.document_ids))

            result = await session.execute(query)
            documents = result.scalars().all()

            # Analyseergebnisse laden
            export_data: list[dict[str, Any]] = []

            for doc in documents:
                # Neuestes Analyseergebnis holen
                result_query = select(AnalysisResult).where(
                    AnalysisResult.document_id == doc.id
                ).order_by(AnalysisResult.created_at.desc()).limit(1)

                ar_result = await session.execute(result_query)
                analysis_result = ar_result.scalar_one_or_none()

                doc_export = {
                    "document_id": doc.id,
                    "filename": doc.original_filename,
                    "status": doc.status.value if doc.status else None,
                    "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                    "extracted_data": doc.extracted_data,
                    "precheck_passed": doc.precheck_passed,
                    "precheck_errors": doc.precheck_errors,
                }

                if analysis_result:
                    doc_export["analysis"] = {
                        "overall_assessment": analysis_result.overall_assessment,
                        "confidence": analysis_result.confidence,
                        "semantic_check": analysis_result.semantic_check,
                        "economic_check": analysis_result.economic_check,
                        "beneficiary_match": analysis_result.beneficiary_match,
                        "warnings": analysis_result.warnings,
                        "provider": analysis_result.provider.value if analysis_result.provider else None,
                        "model": analysis_result.model,
                    }

                export_data.append(doc_export)

            # Export-Verzeichnis erstellen
            export_dir = Path("/data/exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Format bestimmen und exportieren
            export_format = export_job.format or "json"

            if export_format == "json":
                file_path = export_dir / f"{export_job_id}.json"
                file_path.write_text(
                    json.dumps(export_data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8",
                )
            elif export_format == "csv":
                file_path = export_dir / f"{export_job_id}.csv"
                _export_to_csv(export_data, file_path)
            else:
                file_path = export_dir / f"{export_job_id}.json"
                file_path.write_text(
                    json.dumps(export_data, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8",
                )

            # Job aktualisieren
            export_job.status = "COMPLETED"
            export_job.file_path = str(file_path)
            export_job.record_count = len(export_data)
            await session.commit()

            logger.info(f"Exported {len(export_data)} documents to {file_path}")

            return {
                "status": "success",
                "export_job_id": export_job_id,
                "file_path": str(file_path),
                "record_count": len(export_data),
            }

        except Exception as e:
            export_job.status = "FAILED"
            export_job.error_message = str(e)
            await session.commit()
            raise


def _export_to_csv(data: list[dict[str, Any]], file_path: Path):
    """Exportiert Daten als CSV."""
    if not data:
        file_path.write_text("", encoding="utf-8")
        return

    # Flache Struktur erstellen
    rows = []
    for item in data:
        row = {
            "document_id": item.get("document_id"),
            "filename": item.get("filename"),
            "status": item.get("status"),
            "uploaded_at": item.get("uploaded_at"),
            "precheck_passed": item.get("precheck_passed"),
        }

        # Extrahierte Daten flach hinzufügen
        if item.get("extracted_data"):
            for key, val in item["extracted_data"].items():
                if isinstance(val, dict):
                    row[f"extracted_{key}"] = val.get("value")
                else:
                    row[f"extracted_{key}"] = val

        # Analyse-Daten hinzufügen
        if item.get("analysis"):
            analysis = item["analysis"]
            row["analysis_assessment"] = analysis.get("overall_assessment")
            row["analysis_confidence"] = analysis.get("confidence")
            row["analysis_provider"] = analysis.get("provider")

        rows.append(row)

    # CSV schreiben
    if rows:
        fieldnames = list(rows[0].keys())
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        file_path.write_text(output.getvalue(), encoding="utf-8")


# =============================================================================
# Cleanup Task
# =============================================================================


@celery_app.task
def cleanup_old_results():
    """Bereinigt alte Ergebnisse und temporäre Dateien."""
    logger.info("Running cleanup task")

    result = run_async(_cleanup_async())
    return result


async def _cleanup_async() -> dict[str, Any]:
    """Async-Implementation der Bereinigung."""
    cleanup_stats = {
        "temp_files_deleted": 0,
        "old_exports_deleted": 0,
        "old_jobs_cleaned": 0,
    }

    # 1. Temporäre Upload-Dateien älter als 24h löschen
    temp_dir = Path("/data/uploads/temp")
    if temp_dir.exists():
        cutoff_time = datetime.now() - timedelta(hours=24)
        for temp_file in temp_dir.iterdir():
            if temp_file.is_file():
                file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    temp_file.unlink()
                    cleanup_stats["temp_files_deleted"] += 1

    # 2. Export-Dateien älter als 7 Tage löschen
    export_dir = Path("/data/exports")
    if export_dir.exists():
        cutoff_time = datetime.now() - timedelta(days=7)
        for export_file in export_dir.iterdir():
            if export_file.is_file():
                file_mtime = datetime.fromtimestamp(export_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    export_file.unlink()
                    cleanup_stats["old_exports_deleted"] += 1

    # 3. Alte Generator-Outputs älter als 30 Tage löschen
    generated_dir = Path("/data/generated")
    if generated_dir.exists():
        cutoff_time = datetime.now() - timedelta(days=30)
        for job_dir in generated_dir.iterdir():
            if job_dir.is_dir():
                dir_mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
                if dir_mtime < cutoff_time:
                    shutil.rmtree(job_dir)
                    cleanup_stats["old_jobs_cleaned"] += 1

    # 4. Datenbank-Bereinigung (abgeschlossene Jobs älter als 90 Tage)
    celery_session_maker = get_celery_session_maker()
    async with celery_session_maker() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=90)

        # Alte Export-Jobs löschen
        old_exports = await session.execute(
            select(ExportJob).where(
                ExportJob.status == "COMPLETED",
                ExportJob.created_at < cutoff_date,
            )
        )
        for export_job in old_exports.scalars():
            await session.delete(export_job)
            cleanup_stats["old_jobs_cleaned"] += 1

        await session.commit()

    logger.info(f"Cleanup completed: {cleanup_stats}")

    return {
        "status": "success",
        "stats": cleanup_stats,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# =============================================================================
# Pipeline-Task (Kombination von Process + Analyze)
# =============================================================================


@celery_app.task(bind=True, max_retries=2)
def process_and_analyze_task(
    self,
    document_id: str,
    provider: str = "LOCAL_OLLAMA",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Vollständige Pipeline: Parsen, Vorprüfung, LLM-Analyse.

    Args:
        document_id: Dokument-ID
        provider: LLM-Provider
        model: Modell-ID

    Returns:
        Dict mit Gesamtergebnis
    """
    logger.info(f"Running full pipeline for document: {document_id}")

    try:
        # Schritt 1: Verarbeitung
        process_result = run_async(_process_document_async(document_id))

        if process_result.get("status") == "error":
            return process_result

        # Schritt 2: Analyse
        analyze_result = run_async(
            _analyze_document_async(document_id, provider, model)
        )

        return {
            "status": "success",
            "document_id": document_id,
            "process_result": process_result,
            "analyze_result": analyze_result,
        }

    except Exception as e:
        logger.exception(f"Pipeline error for {document_id}: {e}")
        self.retry(exc=e, countdown=180)


# =============================================================================
# Batch Job Tasks
# =============================================================================

@celery_app.task(bind=True, max_retries=3)
def batch_analyze_task(self, job_id: str) -> dict[str, Any]:
    """
    Batch-Analyse mehrerer Dokumente.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Ergebnis der Batch-Verarbeitung
    """
    logger.info(f"Starting batch analyze job: {job_id}")

    try:
        result = run_async(_batch_analyze_async(job_id))
        return result

    except Exception as e:
        logger.exception(f"Batch analyze error for job {job_id}: {e}")
        run_async(_mark_job_failed(job_id, str(e)))
        self.retry(exc=e, countdown=120)


async def _batch_analyze_async(job_id: str) -> dict[str, Any]:
    """
    Asynchrone Batch-Analyse.
    """
    from app.models.batch_job import BatchJob
    from app.models.enums import BatchJobStatus

    session_maker = get_celery_session_maker()

    async with session_maker() as session:
        # Job laden
        result = await session.execute(
            select(BatchJob).where(BatchJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"status": "error", "message": "Job nicht gefunden"}

        # Job starten
        job.mark_started()
        await session.commit()

        try:
            # Parameter extrahieren
            params = job.parameters or {}
            document_ids = params.get("document_ids")
            status_filter = params.get("status_filter", [DocumentStatus.VALIDATED.value])
            provider = params.get("provider")
            model = params.get("model")
            max_concurrent = params.get("max_concurrent", 5)

            # Dokumente laden
            query = select(Document)
            if job.project_id:
                query = query.where(Document.project_id == job.project_id)
            if document_ids:
                query = query.where(Document.id.in_(document_ids))
            elif status_filter:
                query = query.where(Document.status.in_(status_filter))

            doc_result = await session.execute(query)
            documents = doc_result.scalars().all()

            job.total_items = len(documents)
            await session.commit()

            # Dokumente analysieren
            successful = 0
            failed = 0
            errors = []

            for i, doc in enumerate(documents):
                try:
                    # Analyse durchführen
                    analyze_result = await _analyze_document_async(
                        doc.id, provider, model
                    )

                    if analyze_result.get("status") == "success":
                        successful += 1
                    else:
                        failed += 1
                        errors.append({
                            "document_id": doc.id,
                            "filename": doc.original_filename,
                            "error": analyze_result.get("message", "Unbekannter Fehler"),
                        })

                except Exception as e:
                    failed += 1
                    errors.append({
                        "document_id": doc.id,
                        "filename": doc.original_filename,
                        "error": str(e),
                    })

                # Fortschritt aktualisieren
                job.update_progress(
                    processed=i + 1,
                    successful=successful,
                    failed=failed,
                    message=f"Analysiere {doc.original_filename}...",
                )
                await session.commit()

            # Job abschließen
            job.mark_completed(results={
                "total": len(documents),
                "successful": successful,
                "failed": failed,
            })
            job.errors = errors
            await session.commit()

            # Abhängige Jobs starten
            started_dependent_jobs = await _trigger_dependent_jobs(job_id)
            if started_dependent_jobs:
                logger.info(f"Started {len(started_dependent_jobs)} dependent jobs after batch_analyze")

            return {
                "status": "success",
                "job_id": job_id,
                "total": len(documents),
                "successful": successful,
                "failed": failed,
                "started_dependent_jobs": started_dependent_jobs,
            }

        except Exception as e:
            job.mark_failed(str(e))
            await session.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def batch_validate_task(self, job_id: str) -> dict[str, Any]:
    """
    Batch-Validierung mehrerer Dokumente.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Ergebnis der Batch-Verarbeitung
    """
    logger.info(f"Starting batch validate job: {job_id}")

    try:
        result = run_async(_batch_validate_async(job_id))
        return result

    except Exception as e:
        logger.exception(f"Batch validate error for job {job_id}: {e}")
        run_async(_mark_job_failed(job_id, str(e)))
        self.retry(exc=e, countdown=60)


async def _batch_validate_async(job_id: str) -> dict[str, Any]:
    """
    Asynchrone Batch-Validierung.
    """
    from app.models.batch_job import BatchJob

    session_maker = get_celery_session_maker()

    async with session_maker() as session:
        # Job laden
        result = await session.execute(
            select(BatchJob).where(BatchJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"status": "error", "message": "Job nicht gefunden"}

        job.mark_started()
        await session.commit()

        try:
            params = job.parameters or {}
            document_ids = params.get("document_ids")
            revalidate = params.get("revalidate", False)

            # Dokumente laden
            query = select(Document)
            if job.project_id:
                query = query.where(Document.project_id == job.project_id)
            if document_ids:
                query = query.where(Document.id.in_(document_ids))
            elif not revalidate:
                query = query.where(Document.status == DocumentStatus.UPLOADED.value)

            doc_result = await session.execute(query)
            documents = doc_result.scalars().all()

            job.total_items = len(documents)
            await session.commit()

            successful = 0
            failed = 0

            for i, doc in enumerate(documents):
                try:
                    process_result = await _process_document_async(doc.id)
                    if process_result.get("status") == "success":
                        successful += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

                job.update_progress(
                    processed=i + 1,
                    successful=successful,
                    failed=failed,
                )
                await session.commit()

            job.mark_completed(results={
                "total": len(documents),
                "successful": successful,
                "failed": failed,
            })
            await session.commit()

            # Abhängige Jobs starten
            started_dependent_jobs = await _trigger_dependent_jobs(job_id)
            if started_dependent_jobs:
                logger.info(f"Started {len(started_dependent_jobs)} dependent jobs after batch_validate")

            return {
                "status": "success",
                "job_id": job_id,
                "total": len(documents),
                "successful": successful,
                "failed": failed,
                "started_dependent_jobs": started_dependent_jobs,
            }

        except Exception as e:
            job.mark_failed(str(e))
            await session.commit()
            raise


@celery_app.task(bind=True)
def solution_apply_task(self, job_id: str) -> dict[str, Any]:
    """
    Task zum Anwenden einer Lösungsdatei.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Ergebnis
    """
    logger.info(f"Starting solution apply job: {job_id}")
    # Implementierung folgt in Phase 7
    return {"status": "not_implemented", "job_id": job_id}


@celery_app.task(bind=True)
def rag_rebuild_task(self, job_id: str) -> dict[str, Any]:
    """
    Task zum Neuaufbau des RAG-Index.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Ergebnis
    """
    logger.info(f"Starting RAG rebuild job: {job_id}")
    # Implementierung folgt
    return {"status": "not_implemented", "job_id": job_id}


@celery_app.task(bind=True)
def batch_export_task(self, job_id: str) -> dict[str, Any]:
    """
    Task für Batch-Export.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Ergebnis
    """
    logger.info(f"Starting batch export job: {job_id}")
    # Implementierung folgt
    return {"status": "not_implemented", "job_id": job_id}


@celery_app.task(bind=True, max_retries=2)
def batch_generate_task(self, job_id: str) -> dict[str, Any]:
    """
    Batch-Generierung von Test-Dokumenten.

    Generiert Test-Rechnungen mit konfigurierbaren Fehlern und lädt sie
    optional ins Projekt hoch.

    Args:
        job_id: BatchJob-ID

    Returns:
        Dict mit Generierungsergebnis
    """
    logger.info(f"Starting batch generate job: {job_id}")

    try:
        result = run_async(_batch_generate_async(job_id))
        return result

    except Exception as e:
        logger.exception(f"Batch generate error for job {job_id}: {e}")
        run_async(_mark_job_failed(job_id, str(e)))
        self.retry(exc=e, countdown=120)


async def _batch_generate_async(job_id: str) -> dict[str, Any]:
    """
    Asynchrone Batch-Generierung von Test-Dokumenten.
    """
    from app.models.batch_job import BatchJob
    from uuid import uuid4

    session_maker = get_celery_session_maker()

    async with session_maker() as session:
        # Job laden
        result = await session.execute(
            select(BatchJob).where(BatchJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"status": "error", "message": "Job nicht gefunden"}

        # Job starten
        job.mark_started()
        await session.commit()

        try:
            # Parameter extrahieren
            params = job.parameters or {}
            count = params.get("count", 100)
            ruleset_id = params.get("ruleset_id", "DE_USTG")
            templates_enabled = params.get("templates_enabled", ["T1_HANDWERK", "T3_CORPORATE"])
            error_rate_total = params.get("error_rate_total", 5.0)
            severity = params.get("severity", 2)
            alias_noise_probability = params.get("alias_noise_probability", 10.0)
            upload_after_generate = params.get("upload_after_generate", True)
            analyze_after_upload = params.get("analyze_after_upload", False)

            # Zusätzliche Parameter (optional)
            beneficiary_data = params.get("beneficiary_data")
            project_context = params.get("project_context")
            date_format_profiles = params.get("date_format_profiles", ["DD.MM.YYYY"])
            per_feature_error_rates = params.get("per_feature_error_rates", {})

            job.total_items = count
            await session.commit()

            # Ausgabeverzeichnis erstellen
            output_dir = Path(f"/data/generated/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            generated_files: list[str] = []
            solutions: list[dict[str, Any]] = []
            successful = 0
            failed = 0
            errors_list: list[dict[str, Any]] = []

            # Dokumente generieren
            for i in range(count):
                try:
                    template = random.choice(templates_enabled)
                    has_error = random.random() * 100 < error_rate_total

                    # Generiere Rechnungsdaten
                    invoice_data = _generate_invoice_data(
                        template=template,
                        index=i + 1,
                        has_error=has_error,
                        severity=severity,
                        ruleset_id=ruleset_id,
                        beneficiary_data=beneficiary_data,
                        project_context=project_context,
                        date_format_profiles=date_format_profiles,
                        per_feature_error_rates=per_feature_error_rates,
                        alias_noise_probability=alias_noise_probability,
                    )

                    # Zufälliger Dateiname
                    filename = _generate_random_filename(invoice_data, i + 1)
                    filepath = output_dir / filename

                    # PDF erstellen
                    _format_invoice_pdf(invoice_data, filepath)

                    generated_files.append(str(filepath))
                    successful += 1

                    # Lösung speichern
                    solutions.append({
                        "filename": filename,
                        "filepath": str(filepath),
                        "template": template,
                        "has_error": has_error,
                        "errors": invoice_data.get("injected_errors", []),
                        "correct_values": invoice_data.get("correct_values", {}),
                        "beneficiary_used": invoice_data.get("beneficiary_used", False),
                        "project_id": invoice_data.get("project_id"),
                    })

                except Exception as e:
                    failed += 1
                    errors_list.append({
                        "index": i + 1,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    logger.warning(f"Error generating invoice {i + 1}: {e}")

                # Fortschritt aktualisieren
                job.update_progress(
                    processed=i + 1,
                    successful=successful,
                    failed=failed,
                    message=f"Generiere Dokument {i + 1}/{count}...",
                )
                await session.commit()

            # Lösungsdatei schreiben
            solutions_file = output_dir / "solutions.json"
            solutions_file.write_text(
                json.dumps(solutions, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            # Fehler-Übersichtsdatei erstellen
            error_overview_file = output_dir / "fehler_uebersicht.txt"
            error_overview_content = _create_error_overview(solutions, ruleset_id)
            error_overview_file.write_text(error_overview_content, encoding="utf-8")

            # Optional: Dokumente hochladen
            uploaded_doc_ids: list[str] = []
            if upload_after_generate and job.project_id:
                import hashlib

                job.update_progress(
                    processed=count,
                    successful=successful,
                    failed=failed,
                    message="Lade Dokumente ins Projekt hoch...",
                )
                await session.commit()

                for solution in solutions:
                    try:
                        filepath = Path(solution["filepath"])
                        if filepath.exists():
                            # SHA256 berechnen
                            sha256_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()

                            # Dokument in DB erstellen
                            doc = Document(
                                id=str(uuid4()),
                                project_id=job.project_id,
                                filename=solution["filename"],
                                original_filename=solution["filename"],
                                sha256=sha256_hash,
                                storage_path=str(filepath),
                                file_size_bytes=filepath.stat().st_size,
                                mime_type="application/pdf",
                                status=DocumentStatus.UPLOADED,
                                ruleset_id=ruleset_id,
                                extracted_data={
                                    "generated": True,
                                    "generator_job_id": job_id,
                                    "template": solution["template"],
                                    "has_error": solution["has_error"],
                                    "injected_errors": solution["errors"],
                                },
                            )
                            session.add(doc)
                            uploaded_doc_ids.append(doc.id)
                    except Exception as e:
                        logger.warning(f"Error uploading document {solution['filename']}: {e}")

                await session.commit()

                # Optional: Analyse starten
                if analyze_after_upload and uploaded_doc_ids:
                    job.update_progress(
                        processed=count,
                        successful=successful,
                        failed=failed,
                        message="Starte Analyse der hochgeladenen Dokumente...",
                    )
                    await session.commit()

                    # Neuen Analyse-Job erstellen, der auf diesen Job wartet
                    analyze_job = BatchJob(
                        job_type="BATCH_ANALYZE",
                        project_id=job.project_id,
                        created_by_id=job.created_by_id,
                        parameters={
                            "document_ids": uploaded_doc_ids,
                            "max_concurrent": 5,
                        },
                        depends_on_job_id=job_id,
                        status_message=f"Wartet auf Generierungs-Job {job_id}",
                    )
                    session.add(analyze_job)
                    await session.commit()

            # Job abschließen
            job.mark_completed(results={
                "generated_count": successful,
                "failed_count": failed,
                "output_dir": str(output_dir),
                "solutions_file": str(solutions_file),
                "uploaded_count": len(uploaded_doc_ids),
                "uploaded_doc_ids": uploaded_doc_ids,
            })
            job.errors = errors_list
            await session.commit()

            logger.info(f"Batch generate completed: {successful} documents generated, {len(uploaded_doc_ids)} uploaded")

            # Abhängige Jobs starten
            started_dependent_jobs = await _trigger_dependent_jobs(job_id)
            if started_dependent_jobs:
                logger.info(f"Started {len(started_dependent_jobs)} dependent jobs")

            return {
                "status": "success",
                "job_id": job_id,
                "generated_count": successful,
                "failed_count": failed,
                "output_dir": str(output_dir),
                "uploaded_count": len(uploaded_doc_ids),
                "started_dependent_jobs": started_dependent_jobs,
            }

        except Exception as e:
            job.mark_failed(str(e))
            await session.commit()
            raise


async def _mark_job_failed(job_id: str, error: str) -> None:
    """
    Markiert einen Job als fehlgeschlagen.
    """
    from app.models.batch_job import BatchJob

    session_maker = get_celery_session_maker()

    async with session_maker() as session:
        result = await session.execute(
            select(BatchJob).where(BatchJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job:
            job.mark_failed(error)
            await session.commit()


async def _trigger_dependent_jobs(completed_job_id: str) -> list[str]:
    """
    Startet alle Jobs, die auf den abgeschlossenen Job gewartet haben.

    Args:
        completed_job_id: ID des abgeschlossenen Jobs

    Returns:
        Liste der gestarteten Job-IDs
    """
    from app.models.batch_job import BatchJob
    from app.models.enums import BatchJobStatus

    session_maker = get_celery_session_maker()
    started_jobs: list[str] = []

    async with session_maker() as session:
        # Alle Jobs finden, die auf diesen Job warten
        result = await session.execute(
            select(BatchJob).where(
                BatchJob.depends_on_job_id == completed_job_id,
                BatchJob.status == BatchJobStatus.PENDING.value,
            )
        )
        dependent_jobs = result.scalars().all()

        for job in dependent_jobs:
            try:
                # Task starten
                task = celery_app.send_task(
                    f"app.worker.tasks.{_get_batch_task_name(job.job_type)}",
                    args=[job.id],
                    queue=_get_batch_queue_name(job.job_type),
                )
                job.celery_task_id = task.id
                job.status = BatchJobStatus.QUEUED.value
                job.status_message = f"Gestartet nach Abschluss von Job {completed_job_id}"
                started_jobs.append(job.id)
                logger.info(f"Started dependent job {job.id} (type={job.job_type})")
            except Exception as e:
                logger.error(f"Failed to start dependent job {job.id}: {e}")

        await session.commit()

    return started_jobs


def _get_batch_task_name(job_type: str) -> str:
    """Gibt den Task-Namen für einen Batch-Job-Typ zurück."""
    task_map = {
        "BATCH_GENERATE": "batch_generate_task",
        "BATCH_ANALYZE": "batch_analyze_task",
        "BATCH_VALIDATE": "batch_validate_task",
        "BATCH_EXPORT": "batch_export_task",
        "SOLUTION_APPLY": "solution_apply_task",
        "RAG_REBUILD": "rag_rebuild_task",
    }
    return task_map.get(job_type, "batch_analyze_task")


def _get_batch_queue_name(job_type: str) -> str:
    """Gibt die Queue für einen Batch-Job-Typ zurück."""
    queue_map = {
        "BATCH_GENERATE": "documents",
        "BATCH_ANALYZE": "llm",
        "BATCH_VALIDATE": "documents",
        "BATCH_EXPORT": "export",
        "SOLUTION_APPLY": "documents",
        "RAG_REBUILD": "llm",
    }
    return queue_map.get(job_type, "documents")


@celery_app.task
def cleanup_old_results() -> dict[str, Any]:
    """
    Bereinigt alte Ergebnisse und temporäre Dateien.

    Wird periodisch vom Celery Beat ausgeführt.

    Returns:
        Dict mit Bereinigungsstatistik
    """
    logger.info("Running cleanup task")

    try:
        result = run_async(_cleanup_async())
        return result
    except Exception as e:
        logger.exception(f"Cleanup error: {e}")
        return {"status": "error", "message": str(e)}


async def _cleanup_async() -> dict[str, Any]:
    """
    Asynchrone Bereinigung.
    """
    from datetime import timedelta
    from app.models.batch_job import BatchJob
    from app.models.enums import BatchJobStatus

    session_maker = get_celery_session_maker()
    cleaned_jobs = 0
    cleaned_files = 0

    async with session_maker() as session:
        # Alte abgeschlossene Batch-Jobs löschen (älter als 30 Tage)
        cutoff = datetime.utcnow() - timedelta(days=30)
        result = await session.execute(
            select(BatchJob).where(
                BatchJob.completed_at < cutoff,
                BatchJob.status.in_([
                    BatchJobStatus.COMPLETED.value,
                    BatchJobStatus.FAILED.value,
                    BatchJobStatus.CANCELLED.value,
                ])
            )
        )
        old_jobs = result.scalars().all()

        for job in old_jobs:
            await session.delete(job)
            cleaned_jobs += 1

        await session.commit()

    # Temporäre Dateien bereinigen
    temp_dirs = [
        settings.uploads_path / "temp",
        settings.exports_path / "temp",
    ]

    for temp_dir in temp_dirs:
        if temp_dir.exists():
            for file in temp_dir.iterdir():
                try:
                    if file.is_file():
                        # Dateien älter als 1 Tag löschen
                        if datetime.fromtimestamp(file.stat().st_mtime) < datetime.utcnow() - timedelta(days=1):
                            file.unlink()
                            cleaned_files += 1
                except Exception as e:
                    logger.warning(f"Could not delete {file}: {e}")

    logger.info(f"Cleanup completed: {cleaned_jobs} jobs, {cleaned_files} files")

    return {
        "status": "success",
        "cleaned_jobs": cleaned_jobs,
        "cleaned_files": cleaned_files,
    }
