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
from datetime import UTC, datetime, timedelta
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

            rule_engine = get_rule_engine(document.ruleset_id or "DE_USTG")
            precheck = rule_engine.precheck(parse_result)

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

            # Rule Engine für Precheck
            rule_engine = get_rule_engine(document.ruleset_id or "DE_USTG")
            precheck = rule_engine.precheck(parse_result)

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
                warnings=list(analysis_result.warnings),
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

    # Template-spezifische Daten
    templates_config = {
        "T1_HANDWERK": {
            "supplier": "Meister Müller Handwerk GmbH",
            "supplier_address": "Werkstraße 12, 80333 München",
            "description": "Reparaturarbeiten und Materialkosten",
            "net_range": (500, 5000),
        },
        "T2_SUPERMARKT": {
            "supplier": "Frisch & Gut Lebensmittel",
            "supplier_address": "Marktplatz 1, 10115 Berlin",
            "description": "Lebensmittel und Getränke für Veranstaltung",
            "net_range": (50, 500),
        },
        "T3_CORPORATE": {
            "supplier": "TechSolutions AG",
            "supplier_address": "Innovationsweg 42, 70173 Stuttgart",
            "description": "IT-Beratung und Softwareentwicklung",
            "net_range": (2000, 20000),
        },
        "T4_FREELANCER": {
            "supplier": "Max Mustermann",
            "supplier_address": "Homeoffice-Str. 7, 50667 Köln",
            "description": "Freiberufliche Dienstleistungen",
            "net_range": (500, 3000),
        },
        "T5_MINIMAL": {
            "supplier": "Schnellservice",
            "supplier_address": "Kurzweg 1, 60311 Frankfurt",
            "description": "Diverse Kleinleistungen",
            "net_range": (20, 200),
        },
    }

    config = templates_config.get(template, templates_config["T1_HANDWERK"])

    # Beträge berechnen
    net_amount = round(random.uniform(*config["net_range"]), 2)
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
    elements.append(Spacer(1, 0.8 * cm))

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
