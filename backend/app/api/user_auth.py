# Pfad: /backend/app/api/user_auth.py
"""
FlowAudit User Authentication API

Endpoints für Benutzer-Authentifizierung mit JWT-Tokens.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# OAuth2 Schema für Token-Authentifizierung
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class Token(BaseModel):
    """JWT Token Response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Decoded Token Data."""

    username: str
    exp: datetime


class UserInfo(BaseModel):
    """Benutzer-Info Response."""

    username: str
    is_admin: bool


def _get_demo_users() -> dict[str, tuple[str, bool]]:
    """
    Lädt Demo-Benutzer aus der Konfiguration.

    Returns:
        Dict mit username -> (password, is_admin)
    """
    settings = get_settings()
    users: dict[str, tuple[str, bool]] = {}

    if settings.demo_users:
        for user_entry in settings.demo_users.split(","):
            user_entry = user_entry.strip()
            if ":" in user_entry:
                username, password = user_entry.split(":", 1)
                username = username.strip()
                password = password.strip()
                # Admin-Flag: Benutzer "admin" ist automatisch Admin
                is_admin = username.lower() == "admin"
                users[username] = (password, is_admin)

    return users


def _verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifiziert ein Passwort.

    Im Debug-Modus wird Klartext verglichen.
    In Produktion sollte bcrypt verwendet werden.
    """
    settings = get_settings()

    # Im Debug-Modus: Klartext-Vergleich (nur für Entwicklung!)
    if settings.debug:
        return plain_password == stored_password

    # In Produktion: bcrypt-Vergleich
    # TODO: Implementieren Sie bcrypt für Produktion
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.verify(plain_password, stored_password)

    # Fallback: Klartext (NICHT für Produktion!)
    return plain_password == stored_password


def _create_access_token(username: str, is_admin: bool) -> tuple[str, int]:
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
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    return token, expires_in


def decode_token(token: str) -> TokenData | None:
    """
    Dekodiert und validiert ein JWT Token.

    Returns:
        TokenData oder None wenn ungültig
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        exp_timestamp = payload.get("exp")

        if username is None or exp_timestamp is None:
            return None

        exp = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        return TokenData(username=username, exp=exp)
    except JWTError as e:
        logger.debug(f"JWT error: {e}")
        return None


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserInfo | None:
    """
    Dependency um den aktuellen Benutzer aus dem Token zu extrahieren.

    Returns:
        UserInfo oder None wenn nicht authentifiziert
    """
    if token is None:
        return None

    token_data = decode_token(token)
    if token_data is None:
        return None

    # Prüfe ob Benutzer noch existiert
    users = _get_demo_users()
    if token_data.username not in users:
        return None

    _, is_admin = users[token_data.username]
    return UserInfo(username=token_data.username, is_admin=is_admin)


async def require_authenticated_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserInfo:
    """
    Dependency die authentifizierten Benutzer erfordert.

    Raises:
        HTTPException 401 wenn nicht authentifiziert
    """
    user = await get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Type Aliases für Dependencies
CurrentUser = Annotated[UserInfo | None, Depends(get_current_user)]
RequiredUser = Annotated[UserInfo, Depends(require_authenticated_user)]


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Benutzer-Login mit Username und Passwort.

    Gibt ein JWT Access Token zurück.
    """
    users = _get_demo_users()

    # Benutzer prüfen
    if form_data.username not in users:
        logger.warning(f"Login failed: User '{form_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stored_password, is_admin = users[form_data.username]

    # Passwort prüfen
    if not _verify_password(form_data.password, stored_password):
        logger.warning(f"Login failed: Invalid password for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token erstellen
    access_token, expires_in = _create_access_token(form_data.username, is_admin)

    logger.info(f"User '{form_data.username}' logged in successfully")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/auth/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: RequiredUser,
) -> UserInfo:
    """
    Gibt Informationen zum aktuell angemeldeten Benutzer zurück.
    """
    return current_user


@router.post("/auth/logout")
async def logout(
    current_user: RequiredUser,
) -> dict[str, str]:
    """
    Logout - invalidiert das Token client-seitig.

    Server-seitig wird das Token nicht invalidiert (stateless JWT).
    Der Client sollte das Token aus dem localStorage entfernen.
    """
    logger.info(f"User '{current_user.username}' logged out")
    return {"message": "Successfully logged out"}


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    current_user: RequiredUser,
) -> Token:
    """
    Erneuert das Access Token.

    Erfordert ein gültiges (nicht abgelaufenes) Token.
    """
    users = _get_demo_users()
    _, is_admin = users.get(current_user.username, (None, False))

    access_token, expires_in = _create_access_token(current_user.username, is_admin)

    logger.info(f"Token refreshed for user '{current_user.username}'")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
