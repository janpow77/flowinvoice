# Pfad: /backend/app/worker/tasks.py
"""
FlowAudit Celery Tasks

Hintergrund-Tasks für Dokumentenverarbeitung und Analyse.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from celery import shared_task

from app.config import get_settings
from app.database import async_session_maker
from app.llm import InvoiceAnalysisRequest, get_llm_adapter
from app.models.document import Document
from app.models.enums import DocumentStatus, Provider
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
    async with async_session_maker() as session:
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
            if precheck.passed:
                document.status = DocumentStatus.VALIDATED
            else:
                document.status = DocumentStatus.VALIDATED  # Auch mit Fehlern weiter

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
    async with async_session_maker() as session:
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
                warnings=[w for w in analysis_result.warnings],
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


@celery_app.task(bind=True)
def generate_invoices_task(
    self,
    generator_job_id: str,
) -> dict[str, Any]:
    """
    Generiert Test-Rechnungen.

    Args:
        generator_job_id: Generator-Job-ID

    Returns:
        Dict mit Generierungsergebnis
    """
    logger.info(f"Generating invoices for job: {generator_job_id}")

    # TODO: Implementierung des PDF-Generators
    # Dies wird in einer späteren Phase implementiert

    return {
        "status": "not_implemented",
        "generator_job_id": generator_job_id,
        "message": "Generator wird in Phase 3 implementiert",
    }


@celery_app.task(bind=True)
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
        raise


async def _export_results_async(export_job_id: str) -> dict[str, Any]:
    """Async-Implementation des Exports."""
    from app.models.export import ExportJob

    async with async_session_maker() as session:
        # Job laden
        export_job = await session.get(ExportJob, export_job_id)
        if not export_job:
            raise ValueError(f"Export job not found: {export_job_id}")

        export_job.status = "RUNNING"
        await session.commit()

        try:
            # Ergebnisse sammeln
            # TODO: Implementierung des eigentlichen Exports
            # (JSON, CSV, PDF-Report)

            export_job.status = "COMPLETED"
            export_job.file_path = f"/exports/{export_job_id}.json"
            await session.commit()

            return {
                "status": "success",
                "export_job_id": export_job_id,
                "file_path": export_job.file_path,
            }

        except Exception as e:
            export_job.status = "FAILED"
            export_job.error_message = str(e)
            await session.commit()
            raise


@celery_app.task
def cleanup_old_results():
    """Bereinigt alte Ergebnisse und temporäre Dateien."""
    logger.info("Running cleanup task")

    # TODO: Implementierung der Bereinigung
    # - Alte temporäre Dateien löschen
    # - Abgelaufene Export-Jobs bereinigen

    return {"status": "success", "message": "Cleanup completed"}


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
