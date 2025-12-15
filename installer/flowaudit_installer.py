#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowAudit Universal GUI Installer – Excellent Edition (v3.0)
------------------------------------------------------------
Ziel: ASUS NUC 15 / Ubuntu Desktop (primär), Windows/macOS best effort.

Features:
- Thread-safe Logging (Queue -> UI)
- Docker compose abstraction (docker compose vs docker-compose)
- Robust readiness checks (container status/health/polling)
- Safer admin creation (JSON-escaping)
- Clean UI layout with stepper + status cards + progress bar
- Logo integration from public directory
"""

import os
import re
import sys
import json
import time
import queue
import shutil
import secrets
import logging
import platform
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# Optional: PIL for logo display (graceful fallback if not installed)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# =============================================================================
# KONFIGURATION
# =============================================================================
DEFAULT_REPO = "https://github.com/janpow77/flowinvoice.git"

DEFAULT_CLONE_DIRNAME = "flowaudit_repo"  # Klonen in Unterordner = sauberer als "."

DEFAULT_DOCKER_DIR = "docker"
DEFAULT_ENV_NAME = ".env"
DEFAULT_OVERRIDE_NAME = "docker-compose.override.yml"

# Services aus docker-compose.yml
SERVICE_BACKEND = "backend"
SERVICE_FRONTEND = "frontend"
SERVICE_OLLAMA = "ollama"
SERVICE_DB = "db"
SERVICE_REDIS = "redis"
SERVICE_CHROMADB = "chromadb"
SERVICE_WORKER = "worker"

FRONTEND_URL_HINT = "http://localhost:3000"
BACKEND_URL_HINT = "http://localhost:8000"

LOG_FILE = "installer.log"

# Logo paths (relativ zum Repo-Root)
LOGO_RELATIVE_PATH = "frontend/public/auditlogo.png"
LOGO_SVG_PATH = "frontend/public/auditlogo.svg"

# =============================================================================
# LOGGING (Datei)
# =============================================================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# =============================================================================
# HELFER: Validierung
# =============================================================================
def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://|^git@|^ssh://", url.strip()))


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip())) or email.strip().endswith("@local")


def sanitize_env_value(v: str) -> str:
    """
    Für .env: trimmen, Zeilenumbrüche entfernen, quotes setzen.
    """
    if v is None:
        v = ""
    v = str(v).replace("\r", "").replace("\n", "").strip()
    # Wenn Sonderzeichen enthalten, quoten
    if any(ch in v for ch in [' ', '"', "'", "=", "#", "$", "`"]):
        v = v.replace('"', '\\"')
        return f'"{v}"'
    return v


# =============================================================================
# HELFER: Subprocess
# =============================================================================
class ProcessError(RuntimeError):
    pass


# =============================================================================
# UI APP
# =============================================================================
class FlowAuditInstaller(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("FlowAudit Universal Installer – Excellent Edition v3.0")
        self.minsize(1024, 800)

        # Thread-safe UI logging queue
        self._log_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()

        # Logo image reference (keep to prevent garbage collection)
        self._logo_image = None
        self._logo_small = None

        # State
        self.repo_url = tk.StringVar(value=DEFAULT_REPO)
        self.clone_dir = tk.StringVar(value=str(Path.cwd() / DEFAULT_CLONE_DIRNAME))
        self.detected_repo_root: Path | None = None

        # Detect if running from within the repo
        self._detect_running_location()

        self.db_password = tk.StringVar(value=secrets.token_hex(12))
        self.jwt_secret = tk.StringVar(value=secrets.token_hex(32))
        self.chroma_token = tk.StringVar(value=secrets.token_hex(12))

        self.cloudflare_token = tk.StringVar(value="")

        self.openai_key = tk.StringVar(value="")
        self.gemini_key = tk.StringVar(value="")
        self.anthropic_key = tk.StringVar(value="")

        self.model_choice = tk.StringVar(value="qwen2.5:32b")  # Default
        self.enable_model_pull = tk.BooleanVar(value=True)

        self.admin_user = tk.StringVar(value="admin")
        self.admin_email = tk.StringVar(value="admin@local")
        self.admin_pass = tk.StringVar(value="admin123")

        # GPU Settings
        self.gpu_memory_fraction = tk.StringVar(value="0.8")
        self.ollama_num_gpu = tk.StringVar(value="999")
        self.ollama_container_memory = tk.StringVar(value="16G")

        self.progress = tk.DoubleVar(value=0.0)
        self.status_system = tk.StringVar(value="Ungeprüft")
        self.status_repo = tk.StringVar(value="Ungeprüft")
        self.status_config = tk.StringVar(value="Ungeprüft")
        self.status_deploy = tk.StringVar(value="Ungeprüft")

        # Styles
        self._init_style()

        # Layout
        self._build_ui()

        # Start queue poller
        self.after(120, self._drain_log_queue)

        # Initial system check
        self.after(300, self.check_system)

        self.log("Installer gestartet.", "info")

    def _detect_running_location(self):
        """Detect if running from within the repo structure."""
        cwd = Path.cwd()

        # Check if we're in installer/ directory within repo
        if cwd.name == "installer" and (cwd.parent / ".git").exists():
            self.detected_repo_root = cwd.parent
            self.clone_dir.set(str(cwd.parent))
            return

        # Check if we're in repo root
        if (cwd / ".git").exists() and (cwd / DEFAULT_DOCKER_DIR).exists():
            self.detected_repo_root = cwd
            self.clone_dir.set(str(cwd))
            return

        # Check parent directories
        for parent in cwd.parents:
            if (parent / ".git").exists() and (parent / DEFAULT_DOCKER_DIR).exists():
                self.detected_repo_root = parent
                self.clone_dir.set(str(parent))
                return

    # -------------------------------------------------------------------------
    # STYLE
    # -------------------------------------------------------------------------
    def _init_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("App.TFrame", background="#f7f8fb")
        style.configure("Card.TLabelframe", background="white")
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))

        style.configure("H1.TLabel", font=("Segoe UI", 18, "bold"), foreground="#0f172a", background="#f7f8fb")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#475569", background="#f7f8fb")

        style.configure("Step.TLabel", font=("Segoe UI", 10, "bold"), foreground="#0f172a", background="white")
        style.configure("BadgeOK.TLabel", font=("Segoe UI", 9, "bold"), foreground="#065f46", background="#d1fae5")
        style.configure("BadgeWARN.TLabel", font=("Segoe UI", 9, "bold"), foreground="#92400e", background="#fef3c7")
        style.configure("BadgeERR.TLabel", font=("Segoe UI", 9, "bold"), foreground="#991b1b", background="#fee2e2")

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Ghost.TButton", font=("Segoe UI", 10))
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"))

    # -------------------------------------------------------------------------
    # LOGO
    # -------------------------------------------------------------------------
    def _load_logo(self, max_width: int = 120, max_height: int = 80):
        """Load logo from repo's public directory."""
        if not PIL_AVAILABLE:
            return None

        logo_paths = []

        # Check detected repo root
        if self.detected_repo_root:
            logo_paths.append(self.detected_repo_root / LOGO_RELATIVE_PATH)

        # Check relative to script location
        script_dir = Path(__file__).parent
        logo_paths.append(script_dir.parent / LOGO_RELATIVE_PATH)
        logo_paths.append(script_dir / "auditlogo.png")

        # Check current directory
        logo_paths.append(Path.cwd() / LOGO_RELATIVE_PATH)
        logo_paths.append(Path.cwd() / "auditlogo.png")

        for logo_path in logo_paths:
            if logo_path.exists():
                try:
                    img = Image.open(logo_path)
                    # Resize maintaining aspect ratio
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception as e:
                    self.log(f"Logo laden fehlgeschlagen ({logo_path}): {e}", "warning")

        return None

    # -------------------------------------------------------------------------
    # UI BUILD
    # -------------------------------------------------------------------------
    def _build_ui(self):
        root = ttk.Frame(self, style="App.TFrame", padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        # Header with Logo
        header = ttk.Frame(root, style="App.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))

        # Logo on the left
        logo_frame = ttk.Frame(header, style="App.TFrame")
        logo_frame.pack(side=tk.LEFT, padx=(0, 16))

        self._logo_image = self._load_logo(max_width=80, max_height=60)
        if self._logo_image:
            logo_label = ttk.Label(logo_frame, image=self._logo_image, background="#f7f8fb")
            logo_label.pack()

        left_head = ttk.Frame(header, style="App.TFrame")
        left_head.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left_head, text="FlowAudit Installer", style="H1.TLabel").pack(anchor=tk.W)
        ttk.Label(left_head, text="Git → Konfiguration → Docker Compose → Admin → Optional: Cloudflare / Ollama",
                  style="Sub.TLabel").pack(anchor=tk.W, pady=(3, 0))
        ttk.Label(left_head, text="Optimiert für ASUS NUC 15 / Ubuntu Desktop",
                  style="Sub.TLabel").pack(anchor=tk.W)

        right_head = ttk.Frame(header, style="App.TFrame")
        right_head.pack(side=tk.RIGHT, anchor=tk.E)

        ttk.Button(right_head, text="Log öffnen", style="Ghost.TButton", command=self.open_log_file).pack(side=tk.RIGHT)

        # Main split
        main = ttk.Frame(root, style="App.TFrame")
        main.pack(fill=tk.BOTH, expand=True)

        # Left: Stepper + actions
        sidebar = ttk.Frame(main, style="App.TFrame")
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self._build_stepper(sidebar)

        # Right: Tabs
        content = ttk.Frame(main, style="App.TFrame")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.nb = ttk.Notebook(content)
        self.nb.pack(fill=tk.BOTH, expand=True)

        self.tab_system = ttk.Frame(self.nb, padding=12)
        self.tab_repo = ttk.Frame(self.nb, padding=12)
        self.tab_config = ttk.Frame(self.nb, padding=12)
        self.tab_deploy = ttk.Frame(self.nb, padding=12)
        self.tab_logs = ttk.Frame(self.nb, padding=12)

        self.nb.add(self.tab_system, text="1) System")
        self.nb.add(self.tab_repo, text="2) Repo")
        self.nb.add(self.tab_config, text="3) Konfiguration")
        self.nb.add(self.tab_deploy, text="4) Deployment")
        self.nb.add(self.tab_logs, text="Logs")

        self._build_tab_system()
        self._build_tab_repo()
        self._build_tab_config()
        self._build_tab_deploy()
        self._build_tab_logs()

        # Footer: progress + buttons
        footer = ttk.Frame(root, style="App.TFrame")
        footer.pack(fill=tk.X, pady=(10, 0))

        pb = ttk.Progressbar(footer, variable=self.progress, maximum=100)
        pb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        ttk.Button(footer, text="Beenden", style="Ghost.TButton", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(footer, text="Nächster Schritt →", style="Primary.TButton", command=self.next_step).pack(side=tk.RIGHT, padx=(0, 8))

    def _build_stepper(self, parent):
        # Card with status badges
        card = ttk.LabelFrame(parent, text="Status", style="Card.TLabelframe", padding=12)
        card.pack(fill=tk.X, pady=(0, 10))

        self._step_row(card, "1. System", self.status_system)
        self._step_row(card, "2. Repository", self.status_repo)
        self._step_row(card, "3. Konfiguration", self.status_config)
        self._step_row(card, "4. Deployment", self.status_deploy)

        actions = ttk.LabelFrame(parent, text="Aktionen", style="Card.TLabelframe", padding=12)
        actions.pack(fill=tk.X)

        ttk.Button(actions, text="System prüfen", style="Primary.TButton", command=self.check_system).pack(fill=tk.X, pady=4)
        ttk.Button(actions, text="Repo prüfen", style="Primary.TButton", command=self.detect_repo).pack(fill=tk.X, pady=4)
        ttk.Button(actions, text="Konfig schreiben", style="Primary.TButton", command=self.write_config_files).pack(fill=tk.X, pady=4)
        ttk.Button(actions, text="Deployment starten", style="Primary.TButton", command=self.start_deploy_thread).pack(fill=tk.X, pady=4)

        # Quick actions
        quick = ttk.LabelFrame(parent, text="Quick Actions", style="Card.TLabelframe", padding=12)
        quick.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(quick, text="Alles in einem Schritt", style="Primary.TButton", command=self.run_full_install).pack(fill=tk.X, pady=4)
        ttk.Button(quick, text="Container Status", style="Ghost.TButton", command=self.show_container_status).pack(fill=tk.X, pady=4)

    def _step_row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text=label).pack(side=tk.LEFT)
        badge = ttk.Label(row, textvariable=var, padding=(8, 2))
        badge.pack(side=tk.RIGHT)

        # store for dynamic color updates
        setattr(self, f"_badge_{label}", badge)

    def _set_status(self, which: str, value: str):
        """
        which: system/repo/config/deploy -> var + badge style
        value: OK / WARN / FEHLER / Ungeprüft / Läuft...
        """
        mapping = {
            "system": self.status_system,
            "repo": self.status_repo,
            "config": self.status_config,
            "deploy": self.status_deploy,
        }
        var = mapping[which]
        var.set(value)

        # determine style based on value
        if value.startswith("OK"):
            style = "BadgeOK.TLabel"
        elif value.startswith("WARN"):
            style = "BadgeWARN.TLabel"
        elif value.startswith("FEHLER"):
            style = "BadgeERR.TLabel"
        elif value.startswith("Läuft"):
            style = "BadgeWARN.TLabel"
        else:
            style = "BadgeWARN.TLabel"

        # Apply to corresponding badge
        badge = {
            "system": getattr(self, "_badge_1. System", None),
            "repo": getattr(self, "_badge_2. Repository", None),
            "config": getattr(self, "_badge_3. Konfiguration", None),
            "deploy": getattr(self, "_badge_4. Deployment", None),
        }.get(which)

        if badge:
            badge.configure(style=style)

    def _build_tab_system(self):
        card = ttk.LabelFrame(self.tab_system, text="Systemprüfung", style="Card.TLabelframe", padding=12)
        card.pack(fill=tk.BOTH, expand=True)

        self.sys_text = tk.Text(card, height=14, wrap="word")
        self.sys_text.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(card)
        btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btns, text="System prüfen", style="Primary.TButton", command=self.check_system).pack(side=tk.LEFT)
        ttk.Button(btns, text="Git installieren (Linux)", style="Ghost.TButton", command=self.install_git_linux).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Docker installieren (Linux)", style="Ghost.TButton", command=self.install_docker_linux).pack(side=tk.LEFT, padx=8)

    def _build_tab_repo(self):
        card = ttk.LabelFrame(self.tab_repo, text="Repository", style="Card.TLabelframe", padding=12)
        card.pack(fill=tk.BOTH, expand=True)

        # Repo URL
        row1 = ttk.Frame(card)
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="Repo URL:", width=14).pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.repo_url).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Clone dir
        row2 = ttk.Frame(card)
        row2.pack(fill=tk.X, pady=6)
        ttk.Label(row2, text="Zielordner:", width=14).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.clone_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row2, text="…", width=3, command=self.pick_clone_dir).pack(side=tk.LEFT, padx=(6, 0))

        # Buttons
        btns = ttk.Frame(card)
        btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btns, text="Klonen", style="Primary.TButton", command=self.clone_repo_thread).pack(side=tk.LEFT)
        ttk.Button(btns, text="Pull (Update)", style="Ghost.TButton", command=self.pull_repo_thread).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Repo erkennen", style="Ghost.TButton", command=self.detect_repo).pack(side=tk.LEFT)

        # Info
        self.repo_info = ttk.Label(card, text="Repo-Status: Wird geprüft...", padding=(0, 10))
        self.repo_info.pack(anchor=tk.W)

    def _build_tab_config(self):
        # Scrollable area
        outer = ttk.LabelFrame(self.tab_config, text="Konfiguration", style="Card.TLabelframe", padding=0)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = ttk.Frame(canvas, padding=12)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Secrets
        self._section(inner, "Sicherheit & Datenbank")
        self._field(inner, "DB Passwort", self.db_password)
        self._field(inner, "JWT Secret", self.jwt_secret)
        self._field(inner, "Chroma Token", self.chroma_token)

        # Cloudflare
        self._section(inner, "Cloudflare Tunnel (optional)")
        ttk.Label(inner, text="Sicherer Zugriff von außen ohne Portfreigabe (Token aus Cloudflare Dashboard nötig).",
                  foreground="#475569").pack(anchor=tk.W, pady=(0, 6))
        self._field(inner, "Tunnel Token", self.cloudflare_token, is_secret=True)

        # API keys
        self._section(inner, "KI API Keys (optional)")
        self._field(inner, "OpenAI Key", self.openai_key, is_secret=True)
        self._field(inner, "Gemini Key", self.gemini_key, is_secret=True)
        self._field(inner, "Anthropic Key", self.anthropic_key, is_secret=True)

        # GPU Settings
        self._section(inner, "GPU Einstellungen (NVIDIA RTX)")
        ttk.Label(inner, text="Für ASUS NUC mit RTX 5060 optimiert",
                  foreground="#475569").pack(anchor=tk.W, pady=(0, 6))
        self._field(inner, "GPU Memory Fraction", self.gpu_memory_fraction)
        self._field(inner, "Ollama GPU Layers", self.ollama_num_gpu)
        self._field(inner, "Container Memory", self.ollama_container_memory)

        # Ollama
        self._section(inner, "Lokales KI-Modell (Ollama)")
        ttk.Checkbutton(inner, text="Beim Deployment Modell automatisch herunterladen",
                        variable=self.enable_model_pull).pack(anchor=tk.W, pady=(0, 8))

        models = [
            ("Qwen 2.5 32B (Empfohlen für NUC)", "qwen2.5:32b"),
            ("Qwen 2.5 14B (Schneller)", "qwen2.5:14b"),
            ("Llama 3.1 70B (High-End)", "llama3.1:70b"),
            ("Mistral Small 22B", "mistral-small"),
            ("Keines (nur Cloud APIs)", "none"),
        ]
        for txt, val in models:
            ttk.Radiobutton(inner, text=txt, variable=self.model_choice, value=val).pack(anchor=tk.W, padx=18)

        # Actions
        btns = ttk.Frame(inner)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text="Konfiguration schreiben", style="Primary.TButton", command=self.write_config_files).pack(side=tk.LEFT)
        ttk.Button(btns, text="Secrets neu generieren", style="Ghost.TButton", command=self.regenerate_secrets).pack(side=tk.LEFT, padx=8)

    def _build_tab_deploy(self):
        card = ttk.LabelFrame(self.tab_deploy, text="Deployment & Admin", style="Card.TLabelframe", padding=12)
        card.pack(fill=tk.BOTH, expand=True)

        self._section(card, "Admin Zugang (wird im Backend angelegt)")
        self._field(card, "Username", self.admin_user)
        self._field(card, "Email", self.admin_email)
        self._field(card, "Passwort", self.admin_pass, is_secret=True)

        warn = ttk.Label(card, text="Hinweis: Passwort nach Erststart ändern. Secrets nicht committen!",
                         foreground="#92400e")
        warn.pack(anchor=tk.W, pady=(8, 0))

        # Services info
        self._section(card, "Docker Services")
        services_info = ttk.Label(card,
            text="Services: db, redis, chromadb, ollama, backend, worker, frontend",
            foreground="#475569")
        services_info.pack(anchor=tk.W)

        ports_info = ttk.Label(card,
            text="Ports: Frontend=3000, Backend=8000, DB=5432, Redis=6379, ChromaDB=8001, Ollama=11434",
            foreground="#475569")
        ports_info.pack(anchor=tk.W)

        btns = ttk.Frame(card)
        btns.pack(fill=tk.X, pady=(16, 0))

        ttk.Button(btns, text="Deployment starten", style="Primary.TButton", command=self.start_deploy_thread).pack(side=tk.LEFT)
        ttk.Button(btns, text="Stop (compose down)", style="Danger.TButton", command=self.compose_down_thread).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Logs anzeigen", style="Ghost.TButton", command=lambda: self.nb.select(self.tab_logs)).pack(side=tk.LEFT)

        # Additional actions
        btns2 = ttk.Frame(card)
        btns2.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(btns2, text="Container neu starten", style="Ghost.TButton", command=self.restart_containers_thread).pack(side=tk.LEFT)
        ttk.Button(btns2, text="Nur Admin erstellen", style="Ghost.TButton", command=self.create_admin_only_thread).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns2, text="Nur Modell laden", style="Ghost.TButton", command=self.pull_model_only_thread).pack(side=tk.LEFT)

    def _build_tab_logs(self):
        frame = ttk.LabelFrame(self.tab_logs, text=f"Live Logs (zusätzlich: {LOG_FILE})", style="Card.TLabelframe", padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            frame,
            state="disabled",
            font=("Consolas", 9),
            background="#0b1020",
            foreground="#d1d5db",
            insertbackground="#d1d5db",
            height=20,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # log tags
        self.log_area.tag_config("info", foreground="#d1d5db")
        self.log_area.tag_config("success", foreground="#34d399")
        self.log_area.tag_config("warning", foreground="#fbbf24")
        self.log_area.tag_config("error", foreground="#fb7185")

        tools = ttk.Frame(frame)
        tools.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(tools, text="Log-Datei öffnen", style="Ghost.TButton", command=self.open_log_file).pack(side=tk.LEFT)
        ttk.Button(tools, text="Logs leeren (UI)", style="Ghost.TButton", command=self.clear_log_ui).pack(side=tk.LEFT, padx=8)
        ttk.Button(tools, text="Docker Logs (Backend)", style="Ghost.TButton", command=self.show_docker_logs).pack(side=tk.LEFT)

    # -------------------------------------------------------------------------
    # UI helpers
    # -------------------------------------------------------------------------
    def _section(self, parent, title: str):
        ttk.Label(parent, text=title, font=("Segoe UI", 11, "bold"), foreground="#0f172a").pack(anchor=tk.W, pady=(14, 6))

    def _field(self, parent, label: str, var: tk.StringVar, is_secret: bool = False):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
        ent = ttk.Entry(row, textvariable=var, show="*" if is_secret else "")
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        return ent

    def next_step(self):
        idx = self.nb.index(self.nb.select())
        if idx < (self.nb.index("end") - 1):
            self.nb.select(idx + 1)

    def clear_log_ui(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state="disabled")

    def regenerate_secrets(self):
        self.db_password.set(secrets.token_hex(12))
        self.jwt_secret.set(secrets.token_hex(32))
        self.chroma_token.set(secrets.token_hex(12))
        self.log("Neue Secrets generiert.", "success")

    # -------------------------------------------------------------------------
    # Logging (thread-safe)
    # -------------------------------------------------------------------------
    def log(self, msg: str, level: str = "info"):
        self._log_queue.put((msg, level))

    def _drain_log_queue(self):
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                # UI
                self.log_area.configure(state="normal")
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n", level)
                self.log_area.see(tk.END)
                self.log_area.configure(state="disabled")

                # file logger
                if level == "error":
                    logging.error(msg)
                elif level == "warning":
                    logging.warning(msg)
                else:
                    logging.info(msg)
        except queue.Empty:
            pass

        self.after(120, self._drain_log_queue)

    # -------------------------------------------------------------------------
    # System checks
    # -------------------------------------------------------------------------
    def check_system(self):
        self.progress.set(5)
        lines = []
        ok = True

        py = sys.version.split()[0]
        lines.append(f"Python: {py}")

        # Check PIL
        lines.append(f"PIL/Pillow: {'OK' if PIL_AVAILABLE else 'FEHLT (Logo wird nicht angezeigt)'}")

        git_ok = shutil.which("git") is not None
        docker_ok = shutil.which("docker") is not None
        compose_ok = self._detect_compose() is not None

        lines.append(f"Git: {'OK' if git_ok else 'FEHLT'}")
        lines.append(f"Docker: {'OK' if docker_ok else 'FEHLT'}")
        lines.append(f"Compose: {'OK' if compose_ok else 'FEHLT'}")

        # Check NVIDIA
        nvidia_ok = False
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if result.returncode == 0:
                nvidia_ok = True
                # Extract GPU info
                for line in result.stdout.split("\n"):
                    if "NVIDIA" in line and "RTX" in line:
                        lines.append(f"GPU: {line.strip()}")
                        break
                else:
                    lines.append("GPU: NVIDIA erkannt")
        except FileNotFoundError:
            pass

        lines.append(f"NVIDIA GPU: {'OK' if nvidia_ok else 'Nicht verfügbar (CPU-only Modus)'}")

        # Check Docker group membership
        if platform.system() == "Linux":
            import grp
            try:
                docker_group = grp.getgrnam("docker")
                username = os.environ.get("USER", "")
                in_docker_group = username in docker_group.gr_mem
                lines.append(f"Docker Gruppe: {'OK' if in_docker_group else f'User {username} nicht in docker Gruppe'}")
                if not in_docker_group:
                    lines.append("  → sudo usermod -aG docker $USER && newgrp docker")
            except KeyError:
                lines.append("Docker Gruppe: Nicht gefunden")

        if not git_ok:
            ok = False
            self.log("Git wurde nicht gefunden. Installiere Git oder nutze den Button (Linux).", "warning")
        if not docker_ok:
            ok = False
            self.log("Docker wurde nicht gefunden. Bitte Docker Engine installieren.", "error")
        if not compose_ok:
            ok = False
            self.log("Docker Compose wurde nicht gefunden. Bitte Compose Plugin installieren.", "error")

        # Render in system text
        self.sys_text.delete("1.0", tk.END)
        self.sys_text.insert(tk.END, "\n".join(lines))

        self.progress.set(15)
        if ok:
            self._set_status("system", "OK")
            self.log("Systemprüfung: OK", "success")
        else:
            self._set_status("system", "FEHLER")
            self.log("Systemprüfung: FEHLER – bitte Hinweise prüfen.", "error")

    def install_git_linux(self):
        if platform.system() != "Linux":
            messagebox.showinfo("Hinweis", "Auto-Installation ist hier nur für Linux vorgesehen.")
            return

        def worker():
            try:
                self.log("Starte Git-Installation via apt (sudo erforderlich)...", "warning")
                self._run_process(["sudo", "apt-get", "update"])
                self._run_process(["sudo", "apt-get", "install", "-y", "git"])
                self.log("Git installiert.", "success")
                self.check_system()
            except Exception as e:
                self.log(f"Git-Installation fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def install_docker_linux(self):
        if platform.system() != "Linux":
            messagebox.showinfo("Hinweis", "Auto-Installation ist hier nur für Linux vorgesehen.")
            return

        def worker():
            try:
                self.log("Starte Docker-Installation (sudo erforderlich)...", "warning")
                self._run_process(["sudo", "apt-get", "update"])
                self._run_process(["sudo", "apt-get", "install", "-y", "ca-certificates", "curl"])

                # Add Docker's official GPG key
                self.log("Füge Docker GPG Key hinzu...", "info")
                self._run_process(["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"])

                # Download and add key
                self._run_process([
                    "sudo", "sh", "-c",
                    "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc"
                ])
                self._run_process(["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.asc"])

                # Add repository
                self.log("Füge Docker Repository hinzu...", "info")
                self._run_process([
                    "sudo", "sh", "-c",
                    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null'
                ])

                self._run_process(["sudo", "apt-get", "update"])
                self._run_process(["sudo", "apt-get", "install", "-y",
                    "docker-ce", "docker-ce-cli", "containerd.io",
                    "docker-buildx-plugin", "docker-compose-plugin"])

                # Add user to docker group
                username = os.environ.get("USER", "")
                if username:
                    self._run_process(["sudo", "usermod", "-aG", "docker", username])
                    self.log(f"User {username} zur docker Gruppe hinzugefügt. Bitte neu einloggen!", "warning")

                self.log("Docker installiert.", "success")
                self.check_system()
            except Exception as e:
                self.log(f"Docker-Installation fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    # -------------------------------------------------------------------------
    # Repo handling
    # -------------------------------------------------------------------------
    def pick_clone_dir(self):
        d = filedialog.askdirectory(title="Zielordner für Repo auswählen")
        if d:
            self.clone_dir.set(str(Path(d)))

    def detect_repo(self):
        """
        Ermittelt Repo Root (clone_dir) + prüft ob docker/ existiert.
        """
        target = Path(self.clone_dir.get()).expanduser().resolve()
        self.detected_repo_root = None

        if (target / ".git").exists():
            self.detected_repo_root = target
        else:
            # Falls Nutzer im Arbeitsverzeichnis geklont hat:
            cwd = Path.cwd()
            if (cwd / ".git").exists():
                self.detected_repo_root = cwd
            # Check if running from installer dir
            elif cwd.name == "installer" and (cwd.parent / ".git").exists():
                self.detected_repo_root = cwd.parent

        if not self.detected_repo_root:
            self.repo_info.configure(text="Repo-Status: Kein Repo gefunden. Bitte klonen oder Zielordner korrekt setzen.")
            self._set_status("repo", "WARN")
            self.log("Repo nicht erkannt. Bitte klonen oder Pfad prüfen.", "warning")
            return

        docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
        if not docker_dir.exists():
            self.repo_info.configure(text=f"Repo-Status: Repo erkannt, aber '{DEFAULT_DOCKER_DIR}/' fehlt.")
            self._set_status("repo", "FEHLER")
            self.log(f"Repo erkannt: {self.detected_repo_root} – aber docker/ fehlt.", "error")
            return

        compose_file = docker_dir / "docker-compose.yml"
        if not compose_file.exists():
            self.repo_info.configure(text=f"Repo-Status: Repo erkannt, aber docker-compose.yml fehlt in {docker_dir}.")
            self._set_status("repo", "FEHLER")
            self.log("docker-compose.yml fehlt im docker/ Ordner.", "error")
            return

        self.repo_info.configure(text=f"Repo-Status: OK ({self.detected_repo_root})")
        self._set_status("repo", "OK")
        self.log(f"Repo erkannt: {self.detected_repo_root}", "success")
        self.progress.set(max(self.progress.get(), 30))

    def clone_repo_thread(self):
        url = self.repo_url.get().strip()
        target = Path(self.clone_dir.get()).expanduser().resolve()

        if not is_valid_url(url):
            messagebox.showerror("Fehler", "Repo-URL sieht ungültig aus.")
            return

        def worker():
            try:
                self._set_status("repo", "Läuft…")
                self.log(f"Klonen: {url} → {target}", "info")
                target.mkdir(parents=True, exist_ok=True)

                # Schutz: nicht in nicht-leeres Verzeichnis klonen
                if any(target.iterdir()):
                    # aber erlauben, wenn es schon ein Repo ist
                    if not (target / ".git").exists():
                        raise ProcessError("Zielordner ist nicht leer. Bitte leeren Ordner wählen oder vorhandenes Repo aktualisieren.")

                if (target / ".git").exists():
                    self.log("Zielordner enthält bereits ein Git-Repo. Nutze 'Pull (Update)'.", "warning")
                else:
                    self._run_process(["git", "clone", url, str(target)])
                    self.log("Klonen erfolgreich.", "success")

                self.progress.set(35)
                self.detect_repo()
            except Exception as e:
                self._set_status("repo", "FEHLER")
                self.log(f"Klonen fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def pull_repo_thread(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Kein Repo erkannt. Bitte zuerst klonen oder Repo-Pfad setzen.")

                self._set_status("repo", "Läuft…")
                self.log("Git Pull (Update) ...", "info")
                self._run_process(["git", "pull"], cwd=str(self.detected_repo_root))
                self._set_status("repo", "OK")
                self.log("Update abgeschlossen.", "success")
                self.progress.set(max(self.progress.get(), 40))
            except Exception as e:
                self._set_status("repo", "FEHLER")
                self.log(f"Git Pull fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    # -------------------------------------------------------------------------
    # Config files (.env + override)
    # -------------------------------------------------------------------------
    def write_config_files(self):
        self.detect_repo()
        if not self.detected_repo_root:
            messagebox.showerror("Fehler", "Repo nicht erkannt. Bitte zuerst klonen.")
            return

        docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
        env_path = docker_dir / DEFAULT_ENV_NAME
        override_path = docker_dir / DEFAULT_OVERRIDE_NAME

        # sanitize values
        cf_token = self.cloudflare_token.get().strip()

        env_lines = [
            "# FlowAudit Environment Configuration",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "# Database",
            f"POSTGRES_PASSWORD={sanitize_env_value(self.db_password.get())}",
            "",
            "# Security",
            f"SECRET_KEY={sanitize_env_value(self.jwt_secret.get())}",
            "",
            "# ChromaDB",
            f"CHROMA_TOKEN={sanitize_env_value(self.chroma_token.get())}",
            "",
            "# Ollama",
            "OLLAMA_HOST=http://ollama:11434",
            f"OLLAMA_GPU_MEMORY_FRACTION={sanitize_env_value(self.gpu_memory_fraction.get())}",
            f"OLLAMA_NUM_GPU={sanitize_env_value(self.ollama_num_gpu.get())}",
            f"OLLAMA_CONTAINER_MEMORY={sanitize_env_value(self.ollama_container_memory.get())}",
            "",
            "# Cloud AI API Keys (optional)",
            f"OPENAI_API_KEY={sanitize_env_value(self.openai_key.get())}",
            f"GEMINI_API_KEY={sanitize_env_value(self.gemini_key.get())}",
            f"ANTHROPIC_API_KEY={sanitize_env_value(self.anthropic_key.get())}",
            "",
            "# Cloudflare Tunnel (optional)",
            f"CLOUDFLARE_TUNNEL_TOKEN={sanitize_env_value(cf_token)}",
            "",
            "# Debug",
            "DEBUG=false",
            "LOG_LEVEL=INFO",
            "",
        ]

        env_content = "\n".join(env_lines)

        try:
            env_path.write_text(env_content, encoding="utf-8")
            self.log(f".env geschrieben: {env_path}", "success")
        except Exception as e:
            self._set_status("config", "FEHLER")
            self.log(f".env schreiben fehlgeschlagen: {e}", "error")
            return

        # Override file: only if CF token present
        try:
            if cf_token:
                override_content = """# FlowAudit Docker Compose Override
# Cloudflare Tunnel for secure external access

services:
  tunnel:
    image: cloudflare/cloudflared:latest
    container_name: flowaudit-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - frontend
      - backend
    networks:
      - default

# Hinweis:
# Falls dein Tunnel auf 'localhost:PORT' zugreifen soll und das in Compose nicht klappt,
# kann 'network_mode: host' nötig sein (Linux). Dann hier ergänzen:
#    network_mode: host
"""
                override_path.write_text(override_content, encoding="utf-8")
                self.log(f"Override aktiviert (Cloudflare): {override_path}", "success")
            else:
                if override_path.exists():
                    override_path.unlink()
                    self.log("Override entfernt (kein Cloudflare Token).", "warning")
        except Exception as e:
            self._set_status("config", "FEHLER")
            self.log(f"Override schreiben/entfernen fehlgeschlagen: {e}", "error")
            return

        self._set_status("config", "OK")
        self.progress.set(max(self.progress.get(), 55))
        self.log("Konfiguration: OK", "success")

    # -------------------------------------------------------------------------
    # Docker compose abstraction
    # -------------------------------------------------------------------------
    def _detect_compose(self):
        """
        Returns a base command list for compose:
        - ["docker-compose"] if available
        - ["docker", "compose"] if available
        - None if not found
        """
        if shutil.which("docker-compose"):
            return ["docker-compose"]
        # docker compose plugin
        if shutil.which("docker"):
            try:
                p = subprocess.run(["docker", "compose", "version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if p.returncode == 0:
                    return ["docker", "compose"]
            except Exception:
                pass
        return None

    def _compose(self, *args) -> list[str]:
        base = self._detect_compose()
        if not base:
            raise ProcessError("Docker Compose nicht gefunden (docker compose / docker-compose).")
        return [*base, *args]

    # -------------------------------------------------------------------------
    # Deployment
    # -------------------------------------------------------------------------
    def run_full_install(self):
        """Run complete installation in one step."""
        def worker():
            try:
                self.nb.select(self.tab_logs)
                self.log("=== VOLLSTÄNDIGE INSTALLATION ===", "info")

                # System check
                self.check_system()
                if self.status_system.get().startswith("FEHLER"):
                    raise ProcessError("Systemprüfung nicht OK. Bitte Docker/Compose installieren.")

                # Repo
                self.detect_repo()
                if not self.status_repo.get().startswith("OK"):
                    self.log("Repo wird geklont...", "info")
                    url = self.repo_url.get().strip()
                    target = Path(self.clone_dir.get()).expanduser().resolve()

                    if not (target / ".git").exists():
                        target.mkdir(parents=True, exist_ok=True)
                        self._run_process(["git", "clone", url, str(target)])

                    self.detect_repo()
                    if not self.status_repo.get().startswith("OK"):
                        raise ProcessError("Repo konnte nicht erkannt werden.")

                # Config
                self.write_config_files()
                if not self.status_config.get().startswith("OK"):
                    raise ProcessError("Konfiguration nicht OK.")

                # Deploy
                self._run_deployment()

            except Exception as e:
                self.log(f"Installation fehlgeschlagen: {e}", "error")
                messagebox.showerror("Fehler", f"Installation fehlgeschlagen:\n{e}")

        threading.Thread(target=worker, daemon=True).start()

    def start_deploy_thread(self):
        def worker():
            try:
                self._run_deployment()
            except Exception as e:
                self._set_status("deploy", "FEHLER")
                self.log(f"KRITISCHER FEHLER: {e}", "error")
                messagebox.showerror("Fehler", f"Installation fehlgeschlagen:\n{e}")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def _run_deployment(self):
        """Main deployment logic."""
        self._set_status("deploy", "Läuft…")
        self.progress.set(max(self.progress.get(), 60))

        self.check_system()
        if self.status_system.get().startswith("FEHLER"):
            raise ProcessError("Systemprüfung nicht OK. Bitte Docker/Compose installieren.")

        self.detect_repo()
        if not self.status_repo.get().startswith("OK"):
            raise ProcessError("Repo nicht OK. Bitte Repo klonen/prüfen.")

        self.write_config_files()
        if not self.status_config.get().startswith("OK"):
            raise ProcessError("Konfiguration nicht OK. Bitte prüfen.")

        self.nb.select(self.tab_logs)
        self.log("=== START DEPLOYMENT ===", "info")

        docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR

        # Create data directory
        data_dir = self.detected_repo_root / "data"
        data_dir.mkdir(exist_ok=True)
        self.log(f"Data-Verzeichnis erstellt: {data_dir}", "info")

        # Compose build + up
        self.log("docker compose build ...", "warning")
        self._run_process(self._compose("build"), cwd=str(docker_dir))
        self.progress.set(70)

        self.log("docker compose up -d ...", "warning")
        self._run_process(self._compose("up", "-d"), cwd=str(docker_dir))
        self.progress.set(78)
        self.log("Container gestartet.", "success")

        # Wait for backend ready
        self.log("Warte auf Backend-Readiness (kann einige Minuten dauern)...", "info")
        self._wait_for_service_ready(docker_dir, SERVICE_BACKEND, timeout_sec=300)
        self.log("Backend ist bereit.", "success")
        self.progress.set(85)

        # Optional: Model pull
        if self.enable_model_pull.get():
            model = self.model_choice.get().strip()
            if model and model != "none":
                self.log(f"Ollama Modell wird geladen: {model} (kann lange dauern)...", "warning")
                # only if service exists
                if self._service_exists(docker_dir, SERVICE_OLLAMA):
                    try:
                        self._run_process(
                            self._compose("exec", "-T", SERVICE_OLLAMA, "ollama", "pull", model),
                            cwd=str(docker_dir),
                            timeout=1800  # 30 min timeout for large models
                        )
                        self.log("Modell geladen.", "success")
                    except ProcessError as e:
                        self.log(f"Model Pull fehlgeschlagen (kann später nachgeholt werden): {e}", "warning")
                else:
                    self.log("Ollama Service nicht gefunden – überspringe Model Pull.", "warning")

        self.progress.set(92)

        # Create admin
        self.log("Erzeuge Admin-User ...", "info")
        try:
            self._create_admin_user(docker_dir)
            self.log("Admin-User ist bereit.", "success")
        except ProcessError as e:
            self.log(f"Admin-Erstellung fehlgeschlagen: {e}", "warning")
            self.log("Sie können den Admin später manuell erstellen.", "info")

        self.progress.set(100)
        self._set_status("deploy", "OK")
        self.log("====================================", "success")
        self.log("INSTALLATION ERFOLGREICH", "success")
        self.log("====================================", "success")
        self.log(f"Frontend: {FRONTEND_URL_HINT}", "info")
        self.log(f"Backend API: {BACKEND_URL_HINT}", "info")
        self.log(f"Admin: {self.admin_user.get()} / {self.admin_email.get()}", "info")

        messagebox.showinfo("Fertig", f"Installation erfolgreich!\n\nFrontend: {FRONTEND_URL_HINT}\nBackend: {BACKEND_URL_HINT}")

    def compose_down_thread(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                self.log("docker compose down ...", "warning")
                self._run_process(self._compose("down"), cwd=str(docker_dir))
                self.log("Container gestoppt.", "success")
                self._set_status("deploy", "Gestoppt")
            except Exception as e:
                self.log(f"Stop fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def restart_containers_thread(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                self.log("docker compose restart ...", "warning")
                self._run_process(self._compose("restart"), cwd=str(docker_dir))
                self.log("Container neu gestartet.", "success")
            except Exception as e:
                self.log(f"Restart fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def create_admin_only_thread(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                self._create_admin_user(docker_dir)
                self.log("Admin-User erstellt/aktualisiert.", "success")
            except Exception as e:
                self.log(f"Admin-Erstellung fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def pull_model_only_thread(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                model = self.model_choice.get().strip()

                if not model or model == "none":
                    self.log("Kein Modell ausgewählt.", "warning")
                    return

                self.log(f"Lade Modell: {model} ...", "warning")
                self._run_process(
                    self._compose("exec", "-T", SERVICE_OLLAMA, "ollama", "pull", model),
                    cwd=str(docker_dir),
                    timeout=1800
                )
                self.log("Modell geladen.", "success")
            except Exception as e:
                self.log(f"Model Pull fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def show_container_status(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                self.log("=== Container Status ===", "info")
                self._run_process(self._compose("ps"), cwd=str(docker_dir))
            except Exception as e:
                self.log(f"Status-Abfrage fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def show_docker_logs(self):
        def worker():
            try:
                self.detect_repo()
                if not self.detected_repo_root:
                    raise ProcessError("Repo nicht erkannt.")

                docker_dir = self.detected_repo_root / DEFAULT_DOCKER_DIR
                self.log("=== Backend Logs (letzte 50 Zeilen) ===", "info")
                self._run_process(self._compose("logs", "--tail=50", SERVICE_BACKEND), cwd=str(docker_dir))
            except Exception as e:
                self.log(f"Log-Abfrage fehlgeschlagen: {e}", "error")

        threading.Thread(target=worker, daemon=True).start()
        self.nb.select(self.tab_logs)

    def _service_exists(self, docker_dir: Path, service: str) -> bool:
        """
        Prüft, ob ein Service in compose config existiert.
        """
        try:
            p = subprocess.run(self._compose("config", "--services"),
                               cwd=str(docker_dir),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True)
            if p.returncode != 0:
                return False
            services = [s.strip() for s in p.stdout.splitlines() if s.strip()]
            return service in services
        except Exception:
            return False

    def _wait_for_service_ready(self, docker_dir: Path, service: str, timeout_sec: int = 180):
        """
        Wartet auf Container-Status:
        - versucht zuerst health=healthy (falls Healthcheck vorhanden)
        - sonst wartet auf running
        """
        start = time.time()
        while time.time() - start < timeout_sec:
            # 1) per docker compose ps (JSON ist nicht überall gleich; wir parse text)
            try:
                p = subprocess.run(self._compose("ps"),
                                   cwd=str(docker_dir),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True)
                out = p.stdout.lower()
                if p.returncode == 0:
                    # Heuristik: service name + "healthy" oder "running"
                    if service.lower() in out and ("healthy" in out or ("up" in out and "unhealthy" not in out)):
                        return
            except Exception:
                pass

            elapsed = int(time.time() - start)
            self.log(f"Warte auf {service}... ({elapsed}s/{timeout_sec}s)", "info")
            time.sleep(5)

        raise ProcessError(f"Timeout: Service '{service}' wurde nicht bereit innerhalb von {timeout_sec}s.")

    def _create_admin_user(self, docker_dir: Path):
        # Validierung
        user = self.admin_user.get().strip()
        email = self.admin_email.get().strip()
        pw = self.admin_pass.get()

        if not user:
            raise ProcessError("Admin Username ist leer.")
        if not email or not is_valid_email(email):
            raise ProcessError("Admin E-Mail ist ungültig (oder nutze z.B. admin@local).")
        if not pw or len(pw) < 6:
            raise ProcessError("Admin Passwort ist zu kurz (mind. 6 Zeichen empfohlen).")

        # JSON-escapen, um Quotes/Injection-Probleme zu vermeiden
        j_user = json.dumps(user)
        j_email = json.dumps(email)
        j_pw = json.dumps(pw)

        py_script = f"""
import asyncio
import json
from sqlalchemy import select

from app.database import init_db, get_session_context
from app.models.user import User
from app.core.security import get_password_hash

ADMIN_USER = json.loads({json.dumps(j_user)})
ADMIN_EMAIL = json.loads({json.dumps(j_email)})
ADMIN_PW = json.loads({json.dumps(j_pw)})

async def run():
    await init_db()
    async with get_session_context() as s:
        res = await s.execute(select(User).where(User.username == ADMIN_USER))
        existing = res.scalar_one_or_none()
        if existing:
            print("EXISTS: Admin user already exists")
            return
        s.add(User(
            username=ADMIN_USER,
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PW),
            role="admin",
            is_active=True
        ))
        await s.commit()
        print("CREATED: Admin user created successfully")

if __name__ == "__main__":
    asyncio.run(run())
""".strip()

        # Exec im Backend
        self._run_process(self._compose("exec", "-T", SERVICE_BACKEND, "python", "-c", py_script),
                          cwd=str(docker_dir))

    # -------------------------------------------------------------------------
    # Process runner
    # -------------------------------------------------------------------------
    def _run_process(self, cmd: list[str], cwd: str | None = None, timeout: int | None = None):
        """
        Runs a process and streams output to UI logs (thread-safe).
        """
        self.log(f"$ {' '.join(cmd)}", "info")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
        except FileNotFoundError:
            raise ProcessError(f"Befehl nicht gefunden: {cmd[0]}")

        assert proc.stdout is not None

        start_time = time.time()
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self.log(line, "info")

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                proc.terminate()
                raise ProcessError(f"Timeout nach {timeout}s: {' '.join(cmd)}")

        proc.wait()
        if proc.returncode != 0:
            raise ProcessError(f"Befehl fehlgeschlagen (Exit {proc.returncode}): {' '.join(cmd)}")

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def open_log_file(self):
        path = Path.cwd() / LOG_FILE
        if not path.exists():
            messagebox.showinfo("Info", "Log-Datei existiert noch nicht.")
            return

        # best effort open
        try:
            if platform.system() == "Windows":
                os.startfile(str(path))  # type: ignore
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception:
            messagebox.showinfo("Info", f"Log-Datei: {path}")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    app = FlowAuditInstaller()
    app.mainloop()
