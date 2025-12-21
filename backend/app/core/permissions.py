# Pfad: /backend/app/core/permissions.py
"""
FlowAudit Permission System

Definiert Berechtigungen und Rollen-Zuordnungen für das System.

Rollen:
- admin: Vollzugriff auf alle Funktionen
- schueler: Arbeitet an zugewiesenem Projekt, sieht nur eigenes Projekt
- extern: Eingeschränkter Gastzugang (Generator, freigegebene Projekte)
"""

from enum import Enum


class Permission(str, Enum):
    """Alle verfügbaren Berechtigungen im System."""

    # Nutzerverwaltung
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_READ_ALL = "user:read_all"
    USER_UPDATE = "user:update"
    USER_UPDATE_ALL = "user:update_all"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Projekte
    PROJECT_CREATE = "project:create"
    PROJECT_READ_ALL = "project:read_all"
    PROJECT_READ_OWN = "project:read_own"
    PROJECT_UPDATE_ALL = "project:update_all"
    PROJECT_UPDATE_OWN = "project:update_own"
    PROJECT_DELETE = "project:delete"
    PROJECT_ASSIGN = "project:assign"
    PROJECT_SHARE = "project:share"

    # Dokumente
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_ANALYZE = "document:analyze"
    DOCUMENT_DELETE = "document:delete"

    # Generator
    GENERATOR_USE = "generator:use"
    GENERATOR_CONFIGURE = "generator:configure"

    # Rulesets
    RULESET_READ = "ruleset:read"
    RULESET_MANAGE = "ruleset:manage"

    # Statistiken
    STATS_VIEW_ALL = "stats:view_all"
    STATS_VIEW_OWN = "stats:view_own"

    # Einstellungen
    SETTINGS_PERSONAL = "settings:personal"
    SETTINGS_SYSTEM = "settings:system"
    SETTINGS_LLM = "settings:llm"


# Rollen-Typ
Role = str

# Rollen-Konstanten
ROLE_ADMIN = "admin"
ROLE_SCHUELER = "schueler"
ROLE_EXTERN = "extern"

# Alle gültigen Rollen
VALID_ROLES = frozenset({ROLE_ADMIN, ROLE_SCHUELER, ROLE_EXTERN})


# Berechtigungen pro Rolle
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    ROLE_ADMIN: frozenset({
        # Alle Berechtigungen
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_READ_ALL,
        Permission.USER_UPDATE,
        Permission.USER_UPDATE_ALL,
        Permission.USER_DELETE,
        Permission.USER_MANAGE_ROLES,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ_ALL,
        Permission.PROJECT_READ_OWN,
        Permission.PROJECT_UPDATE_ALL,
        Permission.PROJECT_UPDATE_OWN,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_ASSIGN,
        Permission.PROJECT_SHARE,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_ANALYZE,
        Permission.DOCUMENT_DELETE,
        Permission.GENERATOR_USE,
        Permission.GENERATOR_CONFIGURE,
        Permission.RULESET_READ,
        Permission.RULESET_MANAGE,
        Permission.STATS_VIEW_ALL,
        Permission.STATS_VIEW_OWN,
        Permission.SETTINGS_PERSONAL,
        Permission.SETTINGS_SYSTEM,
        Permission.SETTINGS_LLM,
    }),
    ROLE_SCHUELER: frozenset({
        # Eigenes Profil
        Permission.USER_READ,
        Permission.USER_UPDATE,
        # Eigenes Projekt
        Permission.PROJECT_READ_OWN,
        Permission.PROJECT_UPDATE_OWN,
        # Dokumente im eigenen Projekt
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_ANALYZE,
        Permission.DOCUMENT_DELETE,
        # Generator nutzen
        Permission.GENERATOR_USE,
        # Rulesets lesen
        Permission.RULESET_READ,
        # Eigene Statistiken
        Permission.STATS_VIEW_OWN,
        # Persönliche Einstellungen
        Permission.SETTINGS_PERSONAL,
    }),
    ROLE_EXTERN: frozenset({
        # Eigenes Profil (eingeschränkt)
        Permission.USER_READ,
        Permission.USER_UPDATE,
        # Freigegebene Projekte lesen
        Permission.PROJECT_READ_OWN,
        # Dokumente lesen (nur freigegebene)
        Permission.DOCUMENT_READ,
        # Generator nutzen
        Permission.GENERATOR_USE,
        # Persönliche Einstellungen (Sprache, Theme)
        Permission.SETTINGS_PERSONAL,
    }),
}


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Prüft, ob eine Rolle eine bestimmte Berechtigung hat.

    Args:
        role: Die Rolle des Nutzers (admin, schueler, extern)
        permission: Die zu prüfende Berechtigung

    Returns:
        True wenn die Rolle die Berechtigung hat, sonst False
    """
    role_perms = ROLE_PERMISSIONS.get(role, frozenset())
    return permission in role_perms


def get_permissions(role: Role) -> frozenset[Permission]:
    """
    Gibt alle Berechtigungen einer Rolle zurück.

    Args:
        role: Die Rolle des Nutzers

    Returns:
        Set aller Berechtigungen dieser Rolle
    """
    return ROLE_PERMISSIONS.get(role, frozenset())


def is_valid_role(role: str) -> bool:
    """
    Prüft, ob eine Rolle gültig ist.

    Args:
        role: Die zu prüfende Rolle

    Returns:
        True wenn die Rolle gültig ist
    """
    return role in VALID_ROLES


def get_permission_names(role: Role) -> list[str]:
    """
    Gibt die Namen aller Berechtigungen einer Rolle zurück.

    Args:
        role: Die Rolle des Nutzers

    Returns:
        Liste der Berechtigungsnamen als Strings
    """
    return [p.value for p in get_permissions(role)]
