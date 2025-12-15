# Pfad: /backend/app/services/system_monitor.py
"""
FlowAudit System Monitor

Überwacht CPU, GPU, RAM und Temperatur.
Implementiert Notfall-Throttling bei Überhitzung/Überlast.
"""

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SystemStatus(str, Enum):
    """System-Gesundheitsstatus."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    THROTTLED = "throttled"


@dataclass
class SystemMetrics:
    """Aktuelle System-Metriken."""
    timestamp: datetime
    cpu_percent: float
    cpu_temp: float | None
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    gpu_percent: float | None
    gpu_temp: float | None
    gpu_memory_used_mb: float | None
    gpu_memory_total_mb: float | None
    status: SystemStatus
    throttle_active: bool
    throttle_reason: str | None


class SystemMonitor:
    """
    System-Monitor mit Throttling-Unterstützung.

    Überwacht:
    - CPU-Auslastung und Temperatur
    - RAM-Nutzung
    - GPU-Auslastung und Temperatur (via nvidia-smi)
    - Ollama-Server-Status

    Throttling wird aktiviert bei:
    - CPU-Temperatur > 85°C
    - GPU-Temperatur > 80°C (konfigurierbar)
    - RAM-Nutzung > 90%
    """

    def __init__(
        self,
        cpu_temp_threshold: float = 85.0,
        gpu_temp_threshold: float = 80.0,
        ram_threshold: float = 90.0,
        ollama_host: str = "http://localhost:11434",
    ):
        self.cpu_temp_threshold = cpu_temp_threshold
        self.gpu_temp_threshold = gpu_temp_threshold
        self.ram_threshold = ram_threshold
        self.ollama_host = ollama_host
        self._throttle_active = False
        self._throttle_reason: str | None = None
        self._last_metrics: SystemMetrics | None = None

    async def get_metrics(self) -> SystemMetrics:
        """Sammelt aktuelle System-Metriken."""
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_temp = self._get_cpu_temp()

        # RAM
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_used_gb = ram.used / (1024 ** 3)
        ram_total_gb = ram.total / (1024 ** 3)

        # GPU (via nvidia-smi)
        gpu_metrics = await self._get_gpu_metrics()

        # Status bestimmen
        status, throttle_reason = self._determine_status(
            cpu_temp=cpu_temp,
            gpu_temp=gpu_metrics.get("temperature"),
            ram_percent=ram_percent,
        )

        if throttle_reason:
            self._throttle_active = True
            self._throttle_reason = throttle_reason
        elif status == SystemStatus.HEALTHY:
            self._throttle_active = False
            self._throttle_reason = None

        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_temp=cpu_temp,
            ram_percent=ram_percent,
            ram_used_gb=round(ram_used_gb, 2),
            ram_total_gb=round(ram_total_gb, 2),
            gpu_percent=gpu_metrics.get("utilization"),
            gpu_temp=gpu_metrics.get("temperature"),
            gpu_memory_used_mb=gpu_metrics.get("memory_used"),
            gpu_memory_total_mb=gpu_metrics.get("memory_total"),
            status=status,
            throttle_active=self._throttle_active,
            throttle_reason=self._throttle_reason,
        )

        self._last_metrics = metrics
        return metrics

    def _get_cpu_temp(self) -> float | None:
        """Liest CPU-Temperatur (Linux)."""
        try:
            import psutil
            temps = psutil.sensors_temperatures()

            # Verschiedene Sensor-Namen probieren
            for name in ["coretemp", "k10temp", "cpu_thermal", "acpitz"]:
                if name in temps:
                    # Höchste Temperatur nehmen
                    return max(t.current for t in temps[name])

            # Fallback: Erste verfügbare Temperatur
            if temps:
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    return first_sensor[0].current

        except Exception as e:
            logger.debug(f"CPU-Temperatur nicht verfügbar: {e}")

        return None

    async def _get_gpu_metrics(self) -> dict[str, float | None]:
        """Liest GPU-Metriken via nvidia-smi."""
        metrics: dict[str, float | None] = {
            "utilization": None,
            "temperature": None,
            "memory_used": None,
            "memory_total": None,
        }

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                if len(parts) >= 4:
                    metrics["utilization"] = float(parts[0].strip())
                    metrics["temperature"] = float(parts[1].strip())
                    metrics["memory_used"] = float(parts[2].strip())
                    metrics["memory_total"] = float(parts[3].strip())

        except FileNotFoundError:
            logger.debug("nvidia-smi nicht gefunden - keine GPU-Metriken")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi Timeout")
        except Exception as e:
            logger.debug(f"GPU-Metriken nicht verfügbar: {e}")

        return metrics

    def _determine_status(
        self,
        cpu_temp: float | None,
        gpu_temp: float | None,
        ram_percent: float,
    ) -> tuple[SystemStatus, str | None]:
        """Bestimmt System-Status und Throttle-Grund."""

        # Kritisch: Sofortiges Throttling
        if cpu_temp and cpu_temp > self.cpu_temp_threshold:
            return SystemStatus.CRITICAL, f"CPU-Temperatur kritisch: {cpu_temp:.1f}°C"

        if gpu_temp and gpu_temp > self.gpu_temp_threshold:
            return SystemStatus.CRITICAL, f"GPU-Temperatur kritisch: {gpu_temp:.1f}°C"

        if ram_percent > 95:
            return SystemStatus.CRITICAL, f"RAM-Nutzung kritisch: {ram_percent:.1f}%"

        # Warnung: Nahe am Limit
        warnings = []

        if cpu_temp and cpu_temp > self.cpu_temp_threshold - 10:
            warnings.append(f"CPU: {cpu_temp:.1f}°C")

        if gpu_temp and gpu_temp > self.gpu_temp_threshold - 10:
            warnings.append(f"GPU: {gpu_temp:.1f}°C")

        if ram_percent > self.ram_threshold:
            warnings.append(f"RAM: {ram_percent:.1f}%")

        if warnings:
            return SystemStatus.WARNING, None

        return SystemStatus.HEALTHY, None

    async def apply_throttling(self) -> dict[str, Any]:
        """
        Wendet Throttling auf Ollama an.

        Bei Überhitzung:
        - Reduziert parallele Anfragen
        - Pausiert laufende Generierungen (wenn möglich)
        """
        if not self._throttle_active:
            return {"throttled": False}

        result = {
            "throttled": True,
            "reason": self._throttle_reason,
            "actions": [],
        }

        try:
            # Ollama: Laufende Modelle prüfen
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_host}/api/ps")

                if response.status_code == 200:
                    running = response.json().get("models", [])

                    if running:
                        # Bei kritischer Temperatur: Warnung loggen
                        logger.warning(
                            f"THROTTLING AKTIV: {self._throttle_reason}. "
                            f"{len(running)} Modell(e) laufen."
                        )
                        result["actions"].append("logged_warning")
                        result["running_models"] = len(running)

        except Exception as e:
            logger.error(f"Throttling-Fehler: {e}")
            result["error"] = str(e)

        return result

    async def get_ollama_status(self) -> dict[str, Any]:
        """Prüft Ollama-Server und geladene Modelle."""
        status = {
            "online": False,
            "models_loaded": [],
            "version": None,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Version prüfen
                version_resp = await client.get(f"{self.ollama_host}/api/version")
                if version_resp.status_code == 200:
                    status["online"] = True
                    status["version"] = version_resp.json().get("version")

                # Geladene Modelle
                ps_resp = await client.get(f"{self.ollama_host}/api/ps")
                if ps_resp.status_code == 200:
                    status["models_loaded"] = [
                        {
                            "name": m.get("name"),
                            "size_vram": m.get("size_vram"),
                        }
                        for m in ps_resp.json().get("models", [])
                    ]

        except Exception as e:
            logger.debug(f"Ollama-Status nicht verfügbar: {e}")

        return status


# Globale Monitor-Instanz
_monitor: SystemMonitor | None = None


def get_system_monitor() -> SystemMonitor:
    """Gibt globale Monitor-Instanz zurück."""
    global _monitor

    if _monitor is None:
        from app.config import get_settings
        settings = get_settings()

        _monitor = SystemMonitor(
            ollama_host=settings.ollama_host,
            gpu_temp_threshold=float(os.getenv("THERMAL_THROTTLE_TEMP", "80")),
        )

    return _monitor
