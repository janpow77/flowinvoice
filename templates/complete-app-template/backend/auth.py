# Datei: backend/auth.py
"""
Authentication API Template

Endpoints for user authentication with JWT tokens.
Supports form-based login and Google OAuth.

Copy to: your-project/app/api/auth.py
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust imports to match your project structure
from app.config import get_settings
from app.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


class Token(BaseModel):
    """JWT Token Response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GoogleAuthUrl(BaseModel):
    """Google OAuth URL Response."""
    auth_url: str
    state: str


class GoogleTokenRequest(BaseModel):
    """Google OAuth Token Exchange Request."""
    code: str
    state: str


# In-memory state storage (use Redis in production)
_oauth_states: dict[str, datetime] = {}


def _create_access_token(username: str, role: str) -> tuple[str, int]:
    """Create a JWT access token."""
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


# =============================================================================
# Form-based Login
# =============================================================================

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """
    Login with username and password.
    Returns a JWT access token.
    """
    # Find user in database
    result = await session.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Verify password (implement your password verification)
    # if not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="Incorrect credentials")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token, expires_in = _create_access_token(user.username, user.role)
    logger.info(f"User '{user.username}' logged in successfully")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post("/auth/logout")
async def logout() -> dict[str, str]:
    """Logout - client should remove token from storage."""
    return {"message": "Successfully logged out"}


# =============================================================================
# Google OAuth
# =============================================================================

@router.get("/auth/google/enabled")
async def google_oauth_enabled() -> dict[str, bool]:
    """Check if Google OAuth is configured."""
    settings = get_settings()
    return {
        "enabled": bool(settings.google_client_id and settings.google_client_secret)
    }


@router.get("/auth/google/url", response_model=GoogleAuthUrl)
async def get_google_auth_url() -> GoogleAuthUrl:
    """Generate Google OAuth authorization URL."""
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    # Generate CSRF state
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = datetime.now(UTC) + timedelta(minutes=10)

    # Clean expired states
    now = datetime.now(UTC)
    expired = [s for s, exp in _oauth_states.items() if exp < now]
    for s in expired:
        del _oauth_states[s]

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return GoogleAuthUrl(auth_url=auth_url, state=state)


@router.post("/auth/google/callback", response_model=Token)
async def google_oauth_callback(
    request: GoogleTokenRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Process Google OAuth callback."""
    settings = get_settings()

    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # Verify state (CSRF protection)
    if request.state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")

    state_expiry = _oauth_states.pop(request.state)
    if datetime.now(UTC) > state_expiry:
        raise HTTPException(status_code=400, detail="State expired")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": request.code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed: {token_response.text}")
            raise HTTPException(status_code=401, detail="Token exchange failed")

        token_data = token_response.json()
        google_token = token_data.get("access_token")

        # Get user info
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to get user info")

        google_user = userinfo_response.json()

    email = google_user.get("email")
    google_id = google_user.get("id")
    name = google_user.get("name", email.split("@")[0] if email else "User")

    if not email:
        raise HTTPException(status_code=400, detail="Email not provided")

    # Find or create user
    result = await session.execute(
        select(User).where((User.email == email) | (User.google_id == google_id))
    )
    user = result.scalar_one_or_none()

    if user:
        if not user.google_id:
            user.google_id = google_id
            await session.commit()
    else:
        # Create new user
        user = User(
            username=email.split("@")[0],
            email=email,
            google_id=google_id,
            full_name=name,
            hashed_password="",
            role="user",
            is_active=True,
            auth_provider="google",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Created new user from Google OAuth: {email}")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    access_token, expires_in = _create_access_token(user.username, user.role)
    logger.info(f"Google OAuth login: {email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )
