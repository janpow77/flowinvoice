# Pfad: /backend/app/api/deps.py
"""
FlowAudit API Dependencies

Authentifizierungs- und Autorisierungs-Dependencies.
Implementiert rollenbasierte Zugriffskontrolle (RBAC).

Rollen:
- admin: Vollzugriff
- schueler: Nur eigenes Projekt
- extern: Eingeschränkter Gastzugang
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.permissions import Permission, has_permission
from app.core.security import ALGORITHM
from app.database import get_async_session

# Alias for compatibility
get_db = get_async_session
from app.models.project import Project
from app.models.project_share import ProjectShare
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
        raise credentials_exception from None

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
    now = datetime.now(UTC)
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


class RequirePermission:
    """
    Dependency-Klasse, die eine bestimmte Berechtigung erfordert.

    Verwendung:
        @router.get("/admin/stats")
        async def get_stats(
            user: Annotated[User, Depends(RequirePermission(Permission.STATS_VIEW_ALL))]
        ):
            ...
    """

    def __init__(self, permission: Permission):
        self.permission = permission

    async def __call__(
        self,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not has_permission(current_user.role, self.permission):
            logger.warning(
                f"User '{current_user.username}' lacks permission '{self.permission.value}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Berechtigung '{self.permission.value}' erforderlich",
            )
        return current_user


class RequireProjectAccess:
    """
    Dependency-Klasse, die Zugriff auf ein bestimmtes Projekt erfordert.

    Prüft je nach Rolle:
    - Admin: Immer Zugriff
    - Schüler: Nur wenn Projekt zugewiesen ist
    - Extern: Nur wenn Projekt freigegeben ist

    Verwendung:
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: str = Path(...),
            user: Annotated[User, Depends(RequireProjectAccess())]
        ):
            ...

        # Mit Schreibzugriff:
        @router.put("/projects/{project_id}")
        async def update_project(
            project_id: str = Path(...),
            user: Annotated[User, Depends(RequireProjectAccess(require_write=True))]
        ):
            ...
    """

    def __init__(self, require_write: bool = False):
        self.require_write = require_write

    async def __call__(
        self,
        project_id: Annotated[str, Path()],
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_async_session)],
    ) -> User:
        # Prüfen ob Zugang noch gültig ist (relevant für Externe)
        if not current_user.has_valid_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Zugang abgelaufen",
            )

        # Admin hat immer Zugriff
        if current_user.is_admin:
            return current_user

        # Schüler: Nur Zugriff auf zugewiesenes Projekt
        if current_user.is_schueler:
            if current_user.assigned_project_id == project_id:
                return current_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kein Zugriff auf dieses Projekt",
            )

        # Extern: Prüfen ob Projekt freigegeben ist
        if current_user.is_extern:
            # Prüfen ob direkt dem Nutzer zugewiesen
            if current_user.assigned_project_id == project_id:
                if self.require_write:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Schreibzugriff nicht erlaubt",
                    )
                return current_user

            # Prüfen ob Projekt explizit freigegeben wurde
            share_query = select(ProjectShare).where(
                ProjectShare.project_id == project_id,
                ProjectShare.user_id == current_user.id,
                or_(
                    ProjectShare.expires_at.is_(None),
                    ProjectShare.expires_at > datetime.now(UTC),
                ),
            )
            result = await session.execute(share_query)
            share = result.scalar_one_or_none()

            if share:
                if self.require_write and share.permissions != "write":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Schreibzugriff nicht erlaubt",
                    )
                return current_user

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kein Zugriff auf dieses Projekt",
            )

        # Unbekannte Rolle
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kein Zugriff auf dieses Projekt",
        )


async def get_accessible_project_ids(
    current_user: User,
    session: AsyncSession,
) -> list[str]:
    """
    Gibt die IDs aller Projekte zurück, auf die der Nutzer Zugriff hat.

    Returns:
        Liste von Projekt-IDs
    """
    # Admin: Alle Projekte
    if current_user.is_admin:
        result = await session.execute(select(Project.id))
        return [row[0] for row in result.fetchall()]

    project_ids: list[str] = []

    # Zugewiesenes Projekt
    if current_user.assigned_project_id:
        project_ids.append(current_user.assigned_project_id)

    # Für Externe: Zusätzlich freigegebene Projekte
    if current_user.is_extern:
        share_query = select(ProjectShare.project_id).where(
            ProjectShare.user_id == current_user.id,
            or_(
                ProjectShare.expires_at.is_(None),
                ProjectShare.expires_at > datetime.now(UTC),
            ),
        )
        result = await session.execute(share_query)
        for row in result.fetchall():
            if row[0] not in project_ids:
                project_ids.append(row[0])

    return project_ids
