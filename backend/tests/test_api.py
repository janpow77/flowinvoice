# Pfad: /backend/tests/test_api.py
"""
FlowAudit API Tests

Tests für REST-API Endpoints.
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    """Test Health-Check Endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_rulesets_list():
    """Test Rulesets-Liste."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/rulesets")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.anyio
async def test_ruleset_detail():
    """Test Ruleset-Details."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/rulesets/DE_USTG")
        # Kann 200 oder 404 sein, je nach Datenbank-Zustand
        assert response.status_code in [200, 404]


@pytest.mark.anyio
async def test_projects_list():
    """Test Projekte-Liste."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.anyio
async def test_documents_list():
    """Test Dokumente-Liste."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.anyio
async def test_llm_providers():
    """Test LLM-Provider-Liste."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/llm/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data


@pytest.mark.anyio
async def test_stats_dashboard():
    """Test Dashboard-Statistiken."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Sollte Statistik-Felder enthalten
        assert "total_documents" in data or "status" in data


@pytest.mark.anyio
async def test_settings_get():
    """Test Einstellungen abrufen."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/settings")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_document_upload_no_file():
    """Test Upload ohne Datei."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/documents/upload")
        assert response.status_code == 422  # Validation Error


@pytest.mark.anyio
async def test_document_not_found():
    """Test nicht existierendes Dokument."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_project_not_found():
    """Test nicht existierendes Projekt."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/projects/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_feedback_submit_invalid():
    """Test ungültiges Feedback."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/feedback", json={
            "document_id": "test",
            "result_id": "test",
            "rating": "INVALID_RATING",  # Ungültig
        })
        assert response.status_code == 422


@pytest.mark.anyio
async def test_rag_search():
    """Test RAG-Suche."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/rag/search", json={
            "query": "Softwareentwicklung",
            "collection_type": "invoices",
            "n_results": 5,
        })
        assert response.status_code == 200


@pytest.mark.anyio
async def test_generator_templates():
    """Test Generator-Templates (Admin)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/generator/templates")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.anyio
async def test_generator_run_non_admin():
    """Test Generator ohne Admin-Rolle."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/generator/run")
        assert response.status_code == 403  # Forbidden
