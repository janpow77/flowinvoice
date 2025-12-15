# Pfad: /backend/app/worker/celery_app.py
"""
FlowAudit Celery App Configuration

Konfiguration der Celery-Anwendung für Hintergrund-Tasks.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "flowaudit",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

# Celery-Konfiguration
celery_app.conf.update(
    # Task-Einstellungen
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Berlin",
    enable_utc=True,
    # Retry-Einstellungen
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Concurrency
    worker_prefetch_multiplier=1,
    # Result-Backend
    result_expires=3600,  # 1 Stunde
    # Task-Routing
    task_routes={
        "app.worker.tasks.process_document_task": {"queue": "documents"},
        "app.worker.tasks.analyze_document_task": {"queue": "llm"},
        "app.worker.tasks.generate_invoices_task": {"queue": "generator"},
        "app.worker.tasks.export_results_task": {"queue": "export"},
    },
    # Beat-Schedule (für periodische Tasks)
    beat_schedule={
        "cleanup-old-results": {
            "task": "app.worker.tasks.cleanup_old_results",
            "schedule": 3600.0,  # Stündlich
        },
    },
)
