# Pfad: /backend/app/api/deps.py
"""
FlowAudit API Dependencies

Authentifizierungs-Dependencies mit Throttled Activity Tracking.
Gemäß Nutzerkonzept Abschnitt 4.4.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import ALGORITHM
from app.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

# OAuth2 Schema für Token-Authentifizierung
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
oauth2_scheme_required = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Performance: Activity Update maximal alle 5 Minuten
ACTIVITY_UPDATE_INTERVAL = timedelta(minutes=5)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme_required)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Dependency um den aktuellen Benutzer aus dem Token zu extrahieren.

    Implementiert Throttled Activity Tracking: last_active_at wird
    maximal alle 5 Minuten aktualisiert um DB-Last zu reduzieren.

    Args:
        token: JWT Bearer Token
        session: Datenbank-Session

    Returns:
        User: Der authentifizierte Benutzer

    Raises:
        HTTPException 401: Token ungültig oder Benutzer nicht gefunden
        HTTPException 400: Benutzer ist deaktiviert
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        logger.debug(f"JWT validation error: {e}")
        raise credentials_exception

    # Benutzer aus Datenbank laden
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User '{username}' from token not found in database")
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    # --- Throttled Activity Tracking ---
    now = datetime.now(timezone.utc)
    should_update = False

    if user.last_active_at is None:
        should_update = True
    elif (now - user.last_active_at) > ACTIVITY_UPDATE_INTERVAL:
        should_update = True

    if should_update:
        user.last_active_at = now
        session.add(user)
        await session.commit()
        logger.debug(f"Updated last_active_at for user '{username}'")
    # -----------------------------------

    return user


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User | None:
    """
    Optionale Benutzer-Dependency.

    Gibt None zurück wenn kein Token vorhanden ist,
    statt eine Exception zu werfen.
    """
    if token is None:
        return None

    try:
        return await get_current_user(token, session)
    except HTTPException:
        return None


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency die Admin-Rechte erfordert.

    Args:
        current_user: Der authentifizierte Benutzer

    Returns:
        User: Der Admin-Benutzer

    Raises:
        HTTPException 403: Benutzer ist kein Admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# Type Aliases für Dependency Injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
