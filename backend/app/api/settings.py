# Pfad: /backend/app/api/settings.py
"""
FlowAudit Settings API

Endpoints für Einstellungen und Provider-Konfiguration.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.models.enums import Provider
from app.models.settings import ApiKey, Setting
from app.schemas.settings import (
    ApiKeyResponse,
    ApiKeySet,
    ModelPullRequest,
    ModelPullResponse,
    OllamaModelsResponse,
    ProviderTestResponse,
    SettingsUpdate,
)

router = APIRouter()
config = get_settings()


@router.get("/settings")
async def get_settings_endpoint(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Gibt aktuelle Einstellungen zurück.

    Returns:
        Vollständige Settings inkl. Provider-Status.
    """
    # Default settings
    settings_dict = {
        "active_provider": "LOCAL_OLLAMA",
        "providers": {
            # Lokale Provider
            "LOCAL_OLLAMA": {
                "enabled": True,
                "category": "local",
                "base_url": config.ollama_host,
                "model_name": config.ollama_default_model,
                "available_models": [config.ollama_default_model],
            },
            "LOCAL_CUSTOM": {
                "enabled": config.local_custom_host is not None,
                "category": "local",
                "base_url": config.local_custom_host,
                "model_name": config.local_custom_model,
                "api_format": config.local_custom_api_format,
                "available_models": [config.local_custom_model] if config.local_custom_host else [],
            },
            # Westliche Cloud-Provider
            "OPENAI": {
                "enabled": config.openai_api_key is not None,
                "category": "western",
                "api_key_is_set": config.openai_api_key is not None,
                "api_key_masked": None,
                "model_name": "gpt-4o-mini",
                "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            },
            "ANTHROPIC": {
                "enabled": config.anthropic_api_key is not None,
                "category": "western",
                "api_key_is_set": config.anthropic_api_key is not None,
                "api_key_masked": None,
                "model_name": "claude-sonnet-4-20250514",
                "available_models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
            },
            "GEMINI": {
                "enabled": config.gemini_api_key is not None,
                "category": "western",
                "api_key_is_set": config.gemini_api_key is not None,
                "api_key_masked": None,
                "model_name": "gemini-1.5-flash",
                "available_models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            },
            # Chinesische Provider
            "ZHIPU_GLM": {
                "enabled": config.zhipu_api_key is not None,
                "category": "chinese",
                "api_key_is_set": config.zhipu_api_key is not None,
                "api_key_masked": None,
                "model_name": "glm-4",
                "available_models": ["glm-4", "glm-4-flash", "glm-4v"],
            },
            "BAIDU_ERNIE": {
                "enabled": config.baidu_api_key is not None and config.baidu_secret_key is not None,
                "category": "chinese",
                "api_key_is_set": config.baidu_api_key is not None,
                "secret_key_is_set": config.baidu_secret_key is not None,
                "api_key_masked": None,
                "model_name": "ernie-4.0-8k",
                "available_models": ["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k"],
            },
            "ALIBABA_QWEN": {
                "enabled": config.alibaba_api_key is not None,
                "category": "chinese",
                "api_key_is_set": config.alibaba_api_key is not None,
                "api_key_masked": None,
                "model_name": "qwen-max",
                "available_models": ["qwen-max", "qwen-plus", "qwen-turbo"],
            },
            "DEEPSEEK": {
                "enabled": config.deepseek_api_key is not None,
                "category": "chinese",
                "api_key_is_set": config.deepseek_api_key is not None,
                "api_key_masked": None,
                "model_name": "deepseek-chat",
                "available_models": ["deepseek-chat", "deepseek-coder"],
            },
        },
        "inference": {
            "temperature": config.default_temperature,
            "max_tokens": config.default_max_tokens,
            "timeout_sec": config.default_timeout_sec,
            "parallel_requests": 2,
            "retry_on_error": True,
            "max_retries": 3,
        },
        "generator": {
            "output_dir": str(config.exports_path),
            "solutions_dir": str(config.exports_path),
            "enable_admin_menu": config.generator_enabled,
        },
        "rag": {
            "enabled": config.rag_enabled,
            "top_k": config.rag_top_k,
            "similarity_threshold": config.rag_similarity_threshold,
            "embedding_model": config.embedding_model,
            "embedding_info": {
                "name": config.embedding_model.split("/")[-1],
                "full_name": config.embedding_model,
                "type": "sentence-transformers",
                "dimensions": 768,  # paraphrase-multilingual-mpnet-base-v2
                "languages": "50+ (inkl. Deutsch)",
                "description": "Multilinguales Embedding-Modell für semantische Ähnlichkeitssuche",
            },
        },
        "logging": {
            "verbose": config.debug,
        },
        "performance": {
            "uvicorn_workers": config.uvicorn_workers,
            "celery_concurrency": config.celery_concurrency,
        },
    }

    # API-Keys aus DB laden
    api_keys_result = await session.execute(select(ApiKey))
    api_keys = api_keys_result.scalars().all()

    for api_key in api_keys:
        provider_name = api_key.provider.value
        if provider_name in settings_dict["providers"]:
            settings_dict["providers"][provider_name]["api_key_is_set"] = True
            settings_dict["providers"][provider_name]["api_key_masked"] = api_key.masked_key
            settings_dict["providers"][provider_name]["enabled"] = True

    return settings_dict


@router.put("/settings")
async def update_settings(
    data: SettingsUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Aktualisiert Einstellungen.

    Args:
        data: Partielle Updates

    Returns:
        Aktualisierte Settings.
    """
    # Settings in DB speichern
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if isinstance(value, dict):
            # Verschachtelte Settings
            for sub_key, sub_value in value.items():
                setting_key = f"{key}.{sub_key}"
                result = await session.execute(
                    select(Setting).where(Setting.key == setting_key)
                )
                setting = result.scalar_one_or_none()

                if setting:
                    setting.value = sub_value
                else:
                    session.add(Setting(key=setting_key, value=sub_value))
        else:
            # Einfache Settings
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = value
            else:
                session.add(Setting(key=key, value=value))

    await session.commit()

    return await get_settings_endpoint(session)


@router.put("/settings/providers/{provider_id}/api-key")
async def set_api_key(
    provider_id: Provider = Path(...),
    data: ApiKeySet = ...,
    session: AsyncSession = Depends(get_async_session),
) -> ApiKeyResponse:
    """
    Setzt API-Key für Provider.

    Args:
        provider_id: Provider (OPENAI, ANTHROPIC, GEMINI)
        data: API-Key

    Returns:
        Bestätigung mit maskiertem Key.
    """
    from cryptography.fernet import Fernet

    # Key verschlüsseln (vereinfacht - in Produktion sicherer)
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.api_key.get_secret_value().encode())

    # Key-Preview (letzte 4 Zeichen)
    raw_key = data.api_key.get_secret_value()
    preview = f"{'*' * (len(raw_key) - 4)}{raw_key[-4:]}"

    # In DB speichern/aktualisieren
    result = await session.execute(select(ApiKey).where(ApiKey.provider == provider_id))
    api_key = result.scalar_one_or_none()

    if api_key:
        api_key.encrypted_key = encrypted
        api_key.key_preview = raw_key[-4:]
    else:
        api_key = ApiKey(
            provider=provider_id,
            encrypted_key=encrypted,
            key_preview=raw_key[-4:],
        )
        session.add(api_key)

    await session.flush()

    return ApiKeyResponse(
        provider=provider_id,
        api_key_is_set=True,
        api_key_masked=preview,
    )


@router.delete("/settings/providers/{provider_id}/api-key")
async def delete_api_key(
    provider_id: Provider = Path(...),
    session: AsyncSession = Depends(get_async_session),
) -> ApiKeyResponse:
    """
    Löscht API-Key für Provider.

    Args:
        provider_id: Provider

    Returns:
        Bestätigung.
    """
    result = await session.execute(select(ApiKey).where(ApiKey.provider == provider_id))
    api_key = result.scalar_one_or_none()

    if api_key:
        await session.delete(api_key)
        await session.flush()

    return ApiKeyResponse(
        provider=provider_id,
        api_key_is_set=False,
        api_key_masked=None,
    )


@router.post("/settings/providers/{provider_id}/test")
async def test_provider(
    provider_id: Provider = Path(...),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderTestResponse:
    """
    Testet Provider-Verbindung.

    Args:
        provider_id: Provider

    Returns:
        Test-Ergebnis.
    """
    import time

    import httpx

    start = time.time()

    try:
        if provider_id == Provider.LOCAL_OLLAMA:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{config.ollama_host}/api/tags")
                latency = int((time.time() - start) * 1000)

                return ProviderTestResponse(
                    provider=provider_id,
                    status="ok" if response.status_code == 200 else "error",
                    model_accessible=response.status_code == 200,
                    latency_ms=latency,
                    message="Connection successful",
                )

        elif provider_id == Provider.OPENAI:
            # OpenAI API-Key aus DB laden
            result = await session.execute(
                select(ApiKey).where(ApiKey.provider == Provider.OPENAI)
            )
            api_key = result.scalar_one_or_none()

            if not api_key and not config.openai_api_key:
                return ProviderTestResponse(
                    provider=provider_id,
                    status="error",
                    model_accessible=False,
                    message="API key not configured",
                )

            key_to_use = config.openai_api_key or "placeholder"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key_to_use}"},
                )
                latency = int((time.time() - start) * 1000)

                return ProviderTestResponse(
                    provider=provider_id,
                    status="ok" if response.status_code == 200 else "error",
                    model_accessible=response.status_code == 200,
                    latency_ms=latency,
                    message="API accessible" if response.status_code == 200 else f"Error: {response.status_code}",
                )

        elif provider_id == Provider.ANTHROPIC:
            result = await session.execute(
                select(ApiKey).where(ApiKey.provider == Provider.ANTHROPIC)
            )
            api_key = result.scalar_one_or_none()

            if not api_key and not config.anthropic_api_key:
                return ProviderTestResponse(
                    provider=provider_id,
                    status="error",
                    model_accessible=False,
                    message="API key not configured",
                )

            key_to_use = config.anthropic_api_key or "placeholder"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key_to_use,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-3-5-haiku-20241022",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}],
                    },
                )
                latency = int((time.time() - start) * 1000)

                # Anthropic gibt 200 oder 401/403 bei ungültigem Key
                is_accessible = response.status_code in [200, 400]
                return ProviderTestResponse(
                    provider=provider_id,
                    status="ok" if is_accessible else "error",
                    model_accessible=is_accessible,
                    latency_ms=latency,
                    message="API accessible" if is_accessible else f"Error: {response.status_code}",
                )

        elif provider_id == Provider.GEMINI:
            result = await session.execute(
                select(ApiKey).where(ApiKey.provider == Provider.GEMINI)
            )
            api_key = result.scalar_one_or_none()

            if not api_key and not config.gemini_api_key:
                return ProviderTestResponse(
                    provider=provider_id,
                    status="error",
                    model_accessible=False,
                    message="API key not configured",
                )

            key_to_use = config.gemini_api_key or "placeholder"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={key_to_use}",
                )
                latency = int((time.time() - start) * 1000)

                return ProviderTestResponse(
                    provider=provider_id,
                    status="ok" if response.status_code == 200 else "error",
                    model_accessible=response.status_code == 200,
                    latency_ms=latency,
                    message="API accessible" if response.status_code == 200 else f"Error: {response.status_code}",
                )

        else:
            return ProviderTestResponse(
                provider=provider_id,
                status="error",
                model_accessible=False,
                message="Unknown provider",
            )

    except Exception as e:
        return ProviderTestResponse(
            provider=provider_id,
            status="error",
            model_accessible=False,
            message=str(e),
        )


@router.get("/settings/providers/LOCAL_OLLAMA/models")
async def list_ollama_models() -> OllamaModelsResponse:
    """
    Listet verfügbare Ollama-Modelle.

    Returns:
        Liste der Modelle.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Modelle abrufen
            response = await client.get(f"{config.ollama_host}/api/tags")

            if response.status_code != 200:
                return OllamaModelsResponse(models=[])

            data = response.json()

            # Geladene Modelle prüfen (über ps-Endpoint)
            loaded_models: set[str] = set()
            try:
                ps_response = await client.get(f"{config.ollama_host}/api/ps")
                if ps_response.status_code == 200:
                    ps_data = ps_response.json()
                    for running_model in ps_data.get("models", []):
                        loaded_models.add(running_model.get("name", ""))
            except Exception:
                pass  # Ignorieren wenn ps nicht verfügbar

            models = [
                {
                    "name": m.get("name"),
                    "size_gb": round(m.get("size", 0) / (1024**3), 2),
                    "loaded": m.get("name") in loaded_models,
                    "modified_at": m.get("modified_at"),
                    "digest": m.get("digest", "")[:12],
                    "parameter_size": m.get("details", {}).get("parameter_size", ""),
                    "quantization": m.get("details", {}).get("quantization_level", ""),
                }
                for m in data.get("models", [])
            ]
            return OllamaModelsResponse(models=models)

    except Exception:
        pass

    return OllamaModelsResponse(models=[])


@router.get("/settings/performance")
async def get_performance_settings() -> dict[str, Any]:
    """
    Gibt aktuelle Performance-Einstellungen zurück.

    Returns:
        Performance-Settings (Worker-Anzahl).
    """
    return {
        "uvicorn_workers": config.uvicorn_workers,
        "celery_concurrency": config.celery_concurrency,
        "min_workers": 1,
        "max_workers": 8,
    }


@router.put("/settings/performance")
async def update_performance_settings(
    uvicorn_workers: int | None = None,
    celery_concurrency: int | None = None,
) -> dict[str, Any]:
    """
    Aktualisiert Performance-Einstellungen.

    Schreibt Werte in .env Datei, die beim nächsten Neustart geladen werden.
    Hinweis: Erfordert Neustart der Container für Änderungen.

    Args:
        uvicorn_workers: Anzahl Uvicorn Worker (1-8)
        celery_concurrency: Anzahl Celery Worker (1-8)

    Returns:
        Aktualisierte Settings + Hinweis auf Neustart.
    """
    from pathlib import Path

    # Validierung
    if uvicorn_workers is not None and not (1 <= uvicorn_workers <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uvicorn_workers must be between 1 and 8",
        )
    if celery_concurrency is not None and not (1 <= celery_concurrency <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="celery_concurrency must be between 1 and 8",
        )

    # .env Datei aktualisieren (im Docker-Verzeichnis)
    env_path = Path("/data/.env.performance")
    env_vars = {}

    # Existierende Werte laden
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val

    # Neue Werte setzen
    if uvicorn_workers is not None:
        env_vars["UVICORN_WORKERS"] = str(uvicorn_workers)
    if celery_concurrency is not None:
        env_vars["CELERY_CONCURRENCY"] = str(celery_concurrency)

    # Datei schreiben
    with open(env_path, "w") as f:
        for key, val in env_vars.items():
            f.write(f"{key}={val}\n")

    return {
        "uvicorn_workers": int(env_vars.get("UVICORN_WORKERS", config.uvicorn_workers)),
        "celery_concurrency": int(env_vars.get("CELERY_CONCURRENCY", config.celery_concurrency)),
        "min_workers": 1,
        "max_workers": 8,
        "restart_required": True,
        "message": "Einstellungen gespeichert. Neustart der Container erforderlich.",
    }


@router.post("/settings/providers/LOCAL_OLLAMA/models/pull")
async def pull_ollama_model(
    data: ModelPullRequest,
) -> ModelPullResponse:
    """
    Lädt Ollama-Modell herunter.

    Args:
        data: Modellname

    Returns:
        Pull-Status.
    """
    import httpx

    try:
        # Starte Pull-Request (non-streaming)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{config.ollama_host}/api/pull",
                json={"name": data.model_name, "stream": False},
            )

            if response.status_code == 200:
                return ModelPullResponse(
                    status="completed",
                    model_name=data.model_name,
                    progress_url=None,
                    message="Model successfully pulled",
                )
            else:
                return ModelPullResponse(
                    status="error",
                    model_name=data.model_name,
                    progress_url=None,
                    message=f"Pull failed: {response.text}",
                )

    except httpx.TimeoutException:
        # Bei Timeout: Pull läuft wahrscheinlich noch
        return ModelPullResponse(
            status="pulling",
            model_name=data.model_name,
            progress_url="/api/settings/providers/LOCAL_OLLAMA/models/pull/status",
            message="Pull started, may take several minutes",
        )

    except Exception as e:
        return ModelPullResponse(
            status="error",
            model_name=data.model_name,
            progress_url=None,
            message=str(e),
        )
