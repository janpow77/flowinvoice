# Pfad: /backend/app/api/auth.py
"""
FlowAudit Authentication Dependencies

Einfache API-Key-basierte Authentifizierung für Admin-Endpoints.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings


def verify_admin_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> bool:
    """
    Verifiziert den Admin-API-Key.

    Args:
        x_api_key: API-Key aus dem X-API-Key Header

    Returns:
        True wenn authentifiziert

    Raises:
        HTTPException: Bei fehlendem oder ungültigem API-Key
    """
    settings = get_settings()

    # Wenn kein API-Key konfiguriert ist (nur Entwicklung!)
    if settings.admin_api_key is None:
        if settings.debug:
            # In Debug-Modus ohne API-Key erlauben (nur für Entwicklung)
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin API key not configured. Set ADMIN_API_KEY environment variable.",
            )

    # API-Key prüfen
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison to prevent timing attacks
    expected_key = settings.admin_api_key.get_secret_value()
    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return True


# Dependency für Admin-Endpoints
AdminAuth = Annotated[bool, Depends(verify_admin_api_key)]
