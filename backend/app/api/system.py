# Pfad: /backend/app/api/system.py
"""
FlowAudit System API

Endpoints für System-Überwachung und GPU-Steuerung.
"""

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.services.system_monitor import get_system_monitor, SystemStatus

router = APIRouter()
config = get_settings()


@router.get("/system/metrics")
async def get_system_metrics() -> dict[str, Any]:
    """
    Gibt aktuelle System-Metriken zurück.

    Returns:
        CPU, RAM, GPU Auslastung und Temperaturen.
    """
    monitor = get_system_monitor()
    metrics = await monitor.get_metrics()

    return {
        "timestamp": metrics.timestamp.isoformat(),
        "cpu": {
            "percent": metrics.cpu_percent,
            "temperature": metrics.cpu_temp,
        },
        "ram": {
            "percent": metrics.ram_percent,
            "used_gb": metrics.ram_used_gb,
            "total_gb": metrics.ram_total_gb,
        },
        "gpu": {
            "percent": metrics.gpu_percent,
            "temperature": metrics.gpu_temp,
            "memory_used_mb": metrics.gpu_memory_used_mb,
            "memory_total_mb": metrics.gpu_memory_total_mb,
        },
        "status": metrics.status.value,
        "throttle": {
            "active": metrics.throttle_active,
            "reason": metrics.throttle_reason,
        },
    }


@router.get("/system/gpu")
async def get_gpu_settings() -> dict[str, Any]:
    """
    Gibt aktuelle GPU-Einstellungen zurück.

    Returns:
        GPU-Konfiguration für Ollama.
    """
    # Aus Umgebungsvariablen oder .env.performance lesen
    env_path = Path("/data/.env.performance")
    env_vars = {}

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val

    return {
        "gpu_enabled": True,  # Standard aktiviert
        "gpu_memory_fraction": float(env_vars.get(
            "OLLAMA_GPU_MEMORY_FRACTION",
            os.getenv("OLLAMA_GPU_MEMORY_FRACTION", "0.8")
        )),
        "num_gpu_layers": int(env_vars.get(
            "OLLAMA_NUM_GPU",
            os.getenv("OLLAMA_NUM_GPU", "999")
        )),
        "num_parallel": int(env_vars.get(
            "OLLAMA_NUM_PARALLEL",
            os.getenv("OLLAMA_NUM_PARALLEL", "2")
        )),
        "context_size": int(env_vars.get(
            "OLLAMA_NUM_CTX",
            os.getenv("OLLAMA_NUM_CTX", "4096")
        )),
        "thermal_throttle_temp": int(env_vars.get(
            "THERMAL_THROTTLE_TEMP",
            os.getenv("THERMAL_THROTTLE_TEMP", "80")
        )),
        "container_memory_limit": env_vars.get(
            "OLLAMA_CONTAINER_MEMORY",
            os.getenv("OLLAMA_CONTAINER_MEMORY", "16G")
        ),
    }


@router.put("/system/gpu")
async def update_gpu_settings(
    gpu_memory_fraction: float | None = None,
    num_gpu_layers: int | None = None,
    num_parallel: int | None = None,
    context_size: int | None = None,
    thermal_throttle_temp: int | None = None,
) -> dict[str, Any]:
    """
    Aktualisiert GPU-Einstellungen.

    Schreibt in .env.performance - erfordert Container-Neustart.

    Args:
        gpu_memory_fraction: GPU-VRAM Anteil (0.1-1.0)
        num_gpu_layers: GPU-Layer (-1=alle, 0=CPU-only, >0=Anzahl)
        num_parallel: Parallele Anfragen (1-4)
        context_size: Kontext-Größe (1024-8192)
        thermal_throttle_temp: Throttle-Temperatur (60-90°C)

    Returns:
        Aktualisierte Settings.
    """
    # Validierung
    if gpu_memory_fraction is not None and not (0.1 <= gpu_memory_fraction <= 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="gpu_memory_fraction must be between 0.1 and 1.0",
        )

    if num_gpu_layers is not None and num_gpu_layers < -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_gpu_layers must be -1 (all) or >= 0",
        )

    if num_parallel is not None and not (1 <= num_parallel <= 4):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_parallel must be between 1 and 4",
        )

    if context_size is not None and not (1024 <= context_size <= 8192):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="context_size must be between 1024 and 8192",
        )

    if thermal_throttle_temp is not None and not (60 <= thermal_throttle_temp <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="thermal_throttle_temp must be between 60 and 90",
        )

    # .env.performance aktualisieren
    env_path = Path("/data/.env.performance")
    env_vars = {}

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val

    # Neue Werte setzen
    if gpu_memory_fraction is not None:
        env_vars["OLLAMA_GPU_MEMORY_FRACTION"] = str(gpu_memory_fraction)
    if num_gpu_layers is not None:
        env_vars["OLLAMA_NUM_GPU"] = str(num_gpu_layers)
    if num_parallel is not None:
        env_vars["OLLAMA_NUM_PARALLEL"] = str(num_parallel)
    if context_size is not None:
        env_vars["OLLAMA_NUM_CTX"] = str(context_size)
    if thermal_throttle_temp is not None:
        env_vars["THERMAL_THROTTLE_TEMP"] = str(thermal_throttle_temp)

    # Datei schreiben
    with open(env_path, "w") as f:
        for key, val in env_vars.items():
            f.write(f"{key}={val}\n")

    return {
        **await get_gpu_settings(),
        "restart_required": True,
        "message": "GPU-Einstellungen gespeichert. Neustart der Container erforderlich.",
    }


@router.get("/system/ollama")
async def get_ollama_status() -> dict[str, Any]:
    """
    Gibt Ollama-Status und geladene Modelle zurück.

    Returns:
        Ollama-Server-Status.
    """
    monitor = get_system_monitor()
    return await monitor.get_ollama_status()


@router.post("/system/throttle/check")
async def check_and_apply_throttling() -> dict[str, Any]:
    """
    Prüft System-Status und wendet ggf. Throttling an.

    Wird automatisch bei kritischen Temperaturen aufgerufen.

    Returns:
        Throttling-Status und durchgeführte Aktionen.
    """
    monitor = get_system_monitor()

    # Aktuelle Metriken holen
    metrics = await monitor.get_metrics()

    # Throttling anwenden wenn nötig
    if metrics.status in [SystemStatus.CRITICAL, SystemStatus.THROTTLED]:
        throttle_result = await monitor.apply_throttling()
        return {
            "status": metrics.status.value,
            "metrics": {
                "cpu_temp": metrics.cpu_temp,
                "gpu_temp": metrics.gpu_temp,
                "ram_percent": metrics.ram_percent,
            },
            "throttling": throttle_result,
        }

    return {
        "status": metrics.status.value,
        "throttling": {"throttled": False},
    }


@router.get("/system/health/detailed")
async def get_detailed_health() -> dict[str, Any]:
    """
    Gibt detaillierten System-Gesundheitsstatus zurück.

    Kombiniert alle System-Checks für Dashboard-Anzeige.

    Returns:
        Vollständiger Gesundheitsstatus.
    """
    monitor = get_system_monitor()

    metrics = await monitor.get_metrics()
    ollama = await monitor.get_ollama_status()

    # Empfehlungen basierend auf Status
    recommendations = []

    if metrics.gpu_temp and metrics.gpu_temp > 75:
        recommendations.append(
            "GPU-Temperatur erhöht. Erwägen Sie niedrigere GPU-Auslastung."
        )

    if metrics.ram_percent > 80:
        recommendations.append(
            "RAM-Nutzung hoch. Reduzieren Sie parallele Anfragen oder Context-Size."
        )

    if not ollama.get("online"):
        recommendations.append(
            "Ollama nicht erreichbar. Prüfen Sie den Container-Status."
        )

    return {
        "overall_status": metrics.status.value,
        "timestamp": metrics.timestamp.isoformat(),
        "cpu": {
            "percent": metrics.cpu_percent,
            "temperature": metrics.cpu_temp,
            "healthy": (metrics.cpu_temp or 0) < 80,
        },
        "ram": {
            "percent": metrics.ram_percent,
            "used_gb": metrics.ram_used_gb,
            "total_gb": metrics.ram_total_gb,
            "healthy": metrics.ram_percent < 85,
        },
        "gpu": {
            "percent": metrics.gpu_percent,
            "temperature": metrics.gpu_temp,
            "memory_used_mb": metrics.gpu_memory_used_mb,
            "memory_total_mb": metrics.gpu_memory_total_mb,
            "healthy": (metrics.gpu_temp or 0) < 75,
        },
        "ollama": ollama,
        "throttle": {
            "active": metrics.throttle_active,
            "reason": metrics.throttle_reason,
        },
        "recommendations": recommendations,
    }
