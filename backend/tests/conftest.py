# Pfad: /backend/tests/conftest.py
"""
FlowAudit Test Configuration

Pytest fixtures und gemeinsame Test-Konfiguration.
"""

import asyncio
from datetime import date
from decimal import Decimal
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app


# Test-Datenbank (In-Memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Erstellt Event Loop für async Tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Erstellt Test-Datenbank-Session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Erstellt Test-HTTP-Client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_invoice_text() -> str:
    """Beispiel-Rechnungstext."""
    return """
RECHNUNG

Rechnungsnummer: 2025-001
Rechnungsdatum: 15.12.2025

Mustermann GmbH
Musterstraße 123
12345 Musterstadt
USt-IdNr.: DE123456789

An:
FlowAudit GmbH
Teststraße 42
10115 Berlin

Leistungszeitraum: 01.12.2025 - 31.12.2025

Leistungsbeschreibung: Softwareentwicklung

Nettobetrag:                1.000,00 €
MwSt. 19%:                    190,00 €
Bruttobetrag:               1.190,00 €

Zahlbar innerhalb von 14 Tagen.

Bankverbindung:
IBAN: DE89370400440532013000
BIC: COBADEFFXXX
"""


@pytest.fixture
def sample_extracted_data() -> dict:
    """Beispiel-extrahierte Daten."""
    return {
        "invoice_number": {
            "value": "2025-001",
            "raw_text": "2025-001",
            "confidence": 0.95,
        },
        "invoice_date": {
            "value": date(2025, 12, 15),
            "raw_text": "15.12.2025",
            "confidence": 0.9,
        },
        "vat_id": {
            "value": "DE123456789",
            "raw_text": "DE123456789",
            "confidence": 0.95,
        },
        "net_amount": {
            "value": Decimal("1000.00"),
            "raw_text": "1.000,00",
            "confidence": 0.9,
        },
        "vat_amount": {
            "value": Decimal("190.00"),
            "raw_text": "190,00",
            "confidence": 0.9,
        },
        "gross_amount": {
            "value": Decimal("1190.00"),
            "raw_text": "1.190,00",
            "confidence": 0.9,
        },
        "vat_rate": {
            "value": 19,
            "raw_text": "19%",
            "confidence": 0.95,
        },
    }


@pytest.fixture
def sample_project_context() -> dict:
    """Beispiel-Projektkontext."""
    return {
        "title": "IT-Modernisierung 2025",
        "description": "Modernisierung der IT-Infrastruktur",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }


@pytest.fixture
def sample_beneficiary_context() -> dict:
    """Beispiel-Begünstigtenkontext."""
    return {
        "name": "FlowAudit GmbH",
        "address": "Teststraße 42, 10115 Berlin",
        "aliases": ["FlowAudit", "Flow Audit GmbH"],
        "implementation_location": "Berlin",
    }
