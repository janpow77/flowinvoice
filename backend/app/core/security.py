# Pfad: /backend/app/core/security.py
"""
FlowAudit Security Core

JWT Token-Erstellung und Passwort-Hashing mit bcrypt.
Gemäß Nutzerkonzept Abschnitt 4.3.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Passwort-Hashing mit bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Konfiguration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 Stunden (Frontend kickt nach 10 Min Inaktivität)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Erstellt ein JWT Access Token.

    Args:
        subject: Der Benutzer (username) als Token-Subject
        expires_delta: Optionale Ablaufzeit, default 8 Stunden

    Returns:
        Encoded JWT Token als String
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifiziert ein Passwort gegen einen bcrypt-Hash.

    Args:
        plain_password: Das eingegebene Klartext-Passwort
        hashed_password: Der gespeicherte bcrypt-Hash

    Returns:
        True wenn das Passwort korrekt ist
    """
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def get_password_hash(password: str) -> str:
    """
    Erstellt einen bcrypt-Hash für ein Passwort.

    Args:
        password: Das Klartext-Passwort

    Returns:
        bcrypt-Hash des Passworts
    """
    hashed: str = pwd_context.hash(password)
    return hashed
