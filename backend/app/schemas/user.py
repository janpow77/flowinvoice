# Pfad: /backend/app/schemas/user.py
"""
FlowAudit User Schemas

Pydantic-Modelle für Benutzer-API.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


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
    language: Literal["de", "en"] = "de"


class UserCreate(UserBase):
    """Schema für Benutzer-Erstellung."""

    password: str = Field(..., min_length=8, max_length=100)
    role: Literal["admin", "user"] = "user"


class UserUpdate(BaseModel):
    """Schema für Benutzer-Aktualisierung."""

    email: EmailStr | None = None
    full_name: str | None = None
    organization: str | None = None
    contact_info: str | None = None
    language: Literal["de", "en"] | None = None
    is_active: bool | None = None


class UserPasswordUpdate(BaseModel):
    """Schema für Passwort-Änderung."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema für Benutzer-Response."""

    id: str
    role: Literal["admin", "user"]
    is_active: bool
    created_at: datetime
    last_active_at: datetime | None = None

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Kompakte Benutzer-Info für Auth-Responses."""

    username: str
    role: str
    is_admin: bool

    class Config:
        from_attributes = True


class ActiveUsersResponse(BaseModel):
    """Response für aktive Benutzer-Statistik."""

    active_users: int
    timestamp: str
