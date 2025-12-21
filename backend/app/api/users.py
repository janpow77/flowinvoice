# Pfad: /backend/app/api/users.py
"""
FlowAudit User Management API

CRUD-Endpunkte für Nutzerverwaltung.
Nur für Admins zugänglich (außer eigenes Profil).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentAdmin, CurrentUser, RequirePermission
from app.core.permissions import Permission, get_permission_names
from app.core.security import get_password_hash, verify_password
from app.database import get_async_session
from app.models.project import Project
from app.models.user import User
from app.schemas.user import (
    UserAdminUpdate,
    UserAssignProject,
    UserCreate,
    UserInfo,
    UserListItem,
    UserListResponse,
    UserPasswordReset,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


# ============================================================================
# Eigenes Profil
# ============================================================================


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserInfo:
    """
    Gibt Informationen über den aktuellen Benutzer zurück.

    Inkl. Berechtigungen für Frontend-Navigation.
    """
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_admin=current_user.is_admin,
        assigned_project_id=current_user.assigned_project_id,
        language=current_user.language,
        theme=current_user.theme,
        permissions=get_permission_names(current_user.role),
    )


@router.get("/me/profile", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> User:
    """Gibt das vollständige Profil des aktuellen Benutzers zurück."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Aktualisiert das eigene Profil.

    Nutzer können nur bestimmte Felder ändern:
    - email, full_name, organization, contact_info
    - language, theme
    """
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    logger.info(f"User '{current_user.username}' updated their profile")
    return current_user


@router.put("/me/password")
async def change_password(
    data: UserPasswordUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Ändert das eigene Passwort."""
    # Aktuelles Passwort prüfen
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch",
        )

    # Neues Passwort setzen
    current_user.hashed_password = get_password_hash(data.new_password)
    session.add(current_user)
    await session.commit()

    logger.info(f"User '{current_user.username}' changed their password")
    return {"message": "Passwort erfolgreich geändert"}


# ============================================================================
# Admin: Nutzerverwaltung
# ============================================================================


@router.get("", response_model=UserListResponse)
async def list_users(
    _admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    role: str | None = Query(None, description="Filter nach Rolle"),
    is_active: bool | None = Query(None, description="Filter nach Status"),
    search: str | None = Query(None, description="Suche in Name/Email/Username"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> UserListResponse:
    """
    Listet alle Benutzer auf (nur Admin).

    Unterstützt Filterung nach Rolle, Status und Volltextsuche.
    """
    query = select(User)

    # Filter anwenden
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.username.ilike(search_pattern))
            | (User.email.ilike(search_pattern))
            | (User.full_name.ilike(search_pattern))
        )

    # Gesamtanzahl
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Paginierte Ergebnisse
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserListItem.model_validate(u) for u in users],
        total=total,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Erstellt einen neuen Benutzer (nur Admin).

    Admin kann Rolle und Projekt-Zuweisung direkt setzen.
    """
    # Prüfen ob Username bereits existiert
    existing = await session.execute(
        select(User).where(User.username == data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Benutzername bereits vergeben",
        )

    # Prüfen ob Email bereits existiert
    existing = await session.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail-Adresse bereits registriert",
        )

    # Projekt-Zuweisung prüfen
    if data.assigned_project_id:
        project = await session.execute(
            select(Project).where(Project.id == data.assigned_project_id)
        )
        if not project.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Projekt nicht gefunden",
            )

    # Benutzer erstellen
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        organization=data.organization,
        contact_info=data.contact_info,
        language=data.language,
        theme=data.theme,
        role=data.role,
        assigned_project_id=data.assigned_project_id,
        access_expires_at=data.access_expires_at,
        invited_by_id=admin.id,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Admin '{admin.username}' created user '{user.username}' with role '{user.role}'")
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: Annotated[str, Path()],
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Gibt einen Benutzer zurück.

    - Admin: Kann alle Benutzer sehen
    - Andere: Nur eigenes Profil
    """
    # Eigenes Profil kann jeder sehen
    if user_id == current_user.id:
        return current_user

    # Fremde Profile nur für Admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Admin kann fremde Profile sehen",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: Annotated[str, Path()],
    data: UserAdminUpdate,
    _admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Aktualisiert einen Benutzer (nur Admin).

    Admin kann alle Felder ändern, inkl. Rolle und Projekt-Zuweisung.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Projekt-Zuweisung prüfen
    if "assigned_project_id" in update_data and update_data["assigned_project_id"]:
        project = await session.execute(
            select(Project).where(Project.id == update_data["assigned_project_id"])
        )
        if not project.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Projekt nicht gefunden",
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Admin updated user '{user.username}'")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: Annotated[str, Path()],
    admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """
    Löscht einen Benutzer (nur Admin).

    Admin kann sich nicht selbst löschen.
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigenen Account kann nicht gelöscht werden",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    username = user.username
    await session.delete(user)
    await session.commit()

    logger.info(f"Admin '{admin.username}' deleted user '{username}'")


@router.put("/{user_id}/password", status_code=status.HTTP_200_OK)
async def reset_user_password(
    user_id: Annotated[str, Path()],
    data: UserPasswordReset,
    admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """
    Setzt das Passwort eines Benutzers zurück (nur Admin).
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    user.hashed_password = get_password_hash(data.new_password)
    session.add(user)
    await session.commit()

    logger.info(f"Admin '{admin.username}' reset password for user '{user.username}'")
    return {"message": "Passwort erfolgreich zurückgesetzt"}


@router.put("/{user_id}/assign-project", response_model=UserResponse)
async def assign_project_to_user(
    user_id: Annotated[str, Path()],
    data: UserAssignProject,
    _admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Weist einem Benutzer ein Projekt zu oder entfernt die Zuweisung.

    Nur Admin kann Projekte zuweisen.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    # Projekt prüfen wenn angegeben
    if data.project_id:
        project = await session.execute(
            select(Project).where(Project.id == data.project_id)
        )
        if not project.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Projekt nicht gefunden",
            )

    user.assigned_project_id = data.project_id
    session.add(user)
    await session.commit()
    await session.refresh(user)

    action = "zugewiesen" if data.project_id else "entfernt"
    logger.info(f"Project assignment {action} for user '{user.username}'")
    return user


@router.put("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: Annotated[str, Path()],
    admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Aktiviert oder deaktiviert einen Benutzer.

    Admin kann sich nicht selbst deaktivieren.
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigenen Account kann nicht deaktiviert werden",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    user.is_active = not user.is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)

    status_text = "aktiviert" if user.is_active else "deaktiviert"
    logger.info(f"Admin '{admin.username}' {status_text} user '{user.username}'")
    return user
