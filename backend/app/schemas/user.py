# Pfad: /backend/app/schemas/user.py
"""
FlowAudit User Schemas

Pydantic-Modelle für Benutzer-API.

Rollen:
- admin: Systemverwaltung, Nutzerverwaltung, voller Zugriff
- schueler: Arbeitet an zugewiesenem Projekt, sieht nur eigenes Projekt
- extern: Eingeschränkter Gastzugang via Cloudflare
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# Rollen-Typen
RoleType = Literal["admin", "schueler", "extern"]
ThemeType = Literal["light", "dark", "system"]
LanguageType = Literal["de", "en"]


class Token(BaseModel):
    """JWT Token Response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded Token Data."""

    username: str | None = None


class UserBase(BaseModel):
    """Basis-Schema für Benutzer."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None
    organization: str | None = None
    contact_info: str | None = None
    language: LanguageType = "de"
    theme: ThemeType = "system"


class UserCreate(UserBase):
    """Schema für Benutzer-Erstellung (nur Admin)."""

    password: str = Field(..., min_length=8, max_length=100)
    role: RoleType = "schueler"
    assigned_project_id: str | None = None
    access_expires_at: datetime | None = None  # Für Externe


class UserUpdate(BaseModel):
    """Schema für Benutzer-Aktualisierung (eigenes Profil)."""

    email: EmailStr | None = None
    full_name: str | None = None
    organization: str | None = None
    contact_info: str | None = None
    language: LanguageType | None = None
    theme: ThemeType | None = None


class UserAdminUpdate(UserUpdate):
    """Schema für Benutzer-Aktualisierung durch Admin."""

    is_active: bool | None = None
    role: RoleType | None = None
    assigned_project_id: str | None = None
    access_expires_at: datetime | None = None


class UserPasswordUpdate(BaseModel):
    """Schema für Passwort-Änderung."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserPasswordReset(BaseModel):
    """Schema für Passwort-Reset durch Admin."""

    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema für Benutzer-Response."""

    id: str
    role: RoleType
    is_active: bool
    assigned_project_id: str | None = None
    access_expires_at: datetime | None = None
    invited_by_id: str | None = None
    created_at: datetime
    last_active_at: datetime | None = None

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """Kompaktes Schema für Benutzer-Liste."""

    id: str
    username: str
    email: str
    full_name: str | None = None
    role: RoleType
    is_active: bool
    assigned_project_id: str | None = None
    last_active_at: datetime | None = None

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Kompakte Benutzer-Info für Auth-Responses."""

    id: str
    username: str
    role: RoleType
    is_admin: bool
    assigned_project_id: str | None = None
    language: LanguageType = "de"
    theme: ThemeType = "system"
    permissions: list[str] = []

    class Config:
        from_attributes = True


class ActiveUsersResponse(BaseModel):
    """Response für aktive Benutzer-Statistik."""

    active_users: int
    timestamp: str


class UserAssignProject(BaseModel):
    """Schema für Projekt-Zuweisung."""

    project_id: str | None = None  # None = Zuweisung entfernen


class UserListResponse(BaseModel):
    """Response für Benutzer-Liste."""

    users: list[UserListItem]
    total: int
