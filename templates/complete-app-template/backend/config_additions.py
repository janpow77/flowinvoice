# Datei: backend/config_additions.py
"""
Configuration Additions for Login Template

Add these fields to your existing Settings class in config.py
"""

from pydantic import Field, SecretStr

# Add to your Settings class:
class SettingsAdditions:
    """
    Copy these fields to your Settings class.

    Example:
        class Settings(BaseSettings):
            # ... your existing fields ...

            # JWT Authentication
            jwt_algorithm: str = "HS256"
            jwt_expire_hours: int = 24
            secret_key: SecretStr = Field(default=SecretStr("change-in-production"))

            # Google OAuth (optional)
            google_client_id: str | None = Field(default=None)
            google_client_secret: SecretStr | None = Field(default=None)
            google_redirect_uri: str = "http://localhost:3000/auth/google/callback"
    """

    # JWT Authentication
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    secret_key: SecretStr = Field(
        default=SecretStr("change-this-in-production"),
        description="Secret key for JWT signing"
    )

    # Google OAuth (optional - set via environment variables)
    google_client_id: str | None = Field(
        default=None,
        description="Google OAuth Client ID"
    )
    google_client_secret: SecretStr | None = Field(
        default=None,
        description="Google OAuth Client Secret"
    )
    google_redirect_uri: str = Field(
        default="http://localhost:3000/auth/google/callback",
        description="Google OAuth redirect URI"
    )


# User model additions
USER_MODEL_ADDITIONS = """
Add these fields to your User model:

    # OAuth Provider (google, github, etc.) - null for local users
    auth_provider: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )
    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
        default=None,
    )
"""


# Environment variables example
ENV_EXAMPLE = """
# .env file example

# JWT Settings
SECRET_KEY=your-super-secret-key-change-in-production
JWT_EXPIRE_HOURS=24

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback
"""

print("Configuration additions for Login Template")
print("=" * 50)
print("\n1. Add to Settings class:")
print("   - jwt_algorithm, jwt_expire_hours, secret_key")
print("   - google_client_id, google_client_secret, google_redirect_uri")
print("\n2. Add to User model:")
print("   - auth_provider (String)")
print("   - google_id (String, unique, indexed)")
print("\n3. Set environment variables:")
print("   - SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, etc.")
