# Pfad: /backend/app/api/user_auth.py
"""
FlowAudit User Authentication API

Endpoints für Benutzer-Authentifizierung mit JWT-Tokens.
Unterstützt datenbankbasierte Authentifizierung und Demo-User-Fallback.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.permissions import get_permission_names
from app.core.security import get_password_hash, verify_password
from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserInfo

logger = logging.getLogger(__name__)
router = APIRouter()


class Token(BaseModel):
    """JWT Token Response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Decoded Token Data."""

    username: str
    exp: datetime


def _get_demo_users() -> dict[str, tuple[str, str]]:
    """
    Lädt Demo-Benutzer aus der Konfiguration.

    Returns:
        Dict mit username -> (password, role)
    """
    settings = get_settings()
    users: dict[str, tuple[str, str]] = {}

    if settings.demo_users:
        for user_entry in settings.demo_users.split(","):
            user_entry = user_entry.strip()
            if ":" in user_entry:
                username, password = user_entry.split(":", 1)
                username = username.strip()
                password = password.strip()
                # Rolle basierend auf Username
                if username.lower() == "admin":
                    role = "admin"
                elif username.lower().startswith("extern"):
                    role = "extern"
                else:
                    role = "schueler"
                users[username] = (password, role)

    return users


def _create_access_token(username: str, role: str) -> tuple[str, int]:
    """
    Erstellt ein JWT Access Token.

    Returns:
        Tuple aus (token, expires_in_seconds)
    """
    settings = get_settings()

    expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    expires_in = settings.jwt_expire_hours * 3600

    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return token, expires_in


async def _authenticate_user(
    username: str,
    password: str,
    session: AsyncSession,
) -> User | None:
    """
    Authentifiziert einen Benutzer gegen die Datenbank.

    Falls kein DB-User gefunden wird und Demo-Mode aktiv ist,
    wird gegen Demo-User geprüft.

    Returns:
        User-Objekt oder None
    """
    settings = get_settings()

    # Zuerst in der Datenbank suchen
    result = await session.execute(
        select(User).where(User.username == username)
    )
    db_user = result.scalar_one_or_none()

    if db_user:
        # Datenbankbenutzer gefunden - Passwort prüfen
        if verify_password(password, db_user.hashed_password):
            if not db_user.is_active:
                logger.warning(f"Login failed: User '{username}' is inactive")
                return None
            if not db_user.has_valid_access:
                logger.warning(f"Login failed: User '{username}' access expired")
                return None
            return db_user
        return None

    # Fallback auf Demo-User (nur im Debug-Modus)
    if settings.debug:
        demo_users = _get_demo_users()
        if username in demo_users:
            stored_password, role = demo_users[username]
            if password == stored_password:
                # Temporären User erstellen (nicht in DB gespeichert)
                logger.info(f"Demo user '{username}' authenticated")
                return User(
                    id="demo-" + username,
                    username=username,
                    email=f"{username}@demo.local",
                    hashed_password="",
                    role=role,
                    is_active=True,
                )

    return None


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """
    Benutzer-Login mit Username und Passwort.

    Gibt ein JWT Access Token zurück.
    Authentifiziert gegen Datenbank oder Demo-User (im Debug-Modus).
    """
    user = await _authenticate_user(
        form_data.username,
        form_data.password,
        session,
    )

    if not user:
        logger.warning(f"Login failed for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token erstellen
    access_token, expires_in = _create_access_token(user.username, user.role)

    logger.info(f"User '{user.username}' logged in successfully (role: {user.role})")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/auth/me", response_model=UserInfo)
async def get_current_user_info(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token: str = Depends(lambda: None),  # Placeholder, actual auth via deps.py
) -> UserInfo:
    """
    Gibt Informationen zum aktuell angemeldeten Benutzer zurück.

    Hinweis: Der eigentliche Endpoint ist /api/users/me
    Dieser Endpoint existiert für Abwärtskompatibilität.
    """
    # Redirect to /api/users/me would be better, but for now just return a hint
    raise HTTPException(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        detail="Use /api/users/me instead",
        headers={"Location": "/api/users/me"},
    )


@router.post("/auth/logout")
async def logout() -> dict[str, str]:
    """
    Logout - invalidiert das Token client-seitig.

    Server-seitig wird das Token nicht invalidiert (stateless JWT).
    Der Client sollte das Token aus dem localStorage entfernen.
    """
    return {"message": "Successfully logged out"}


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """
    Erneuert das Access Token.

    Erfordert ein gültiges (nicht abgelaufenes) Token.
    Verwendet den neuen /api/users/me Endpoint.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented. Re-login required.",
    )
