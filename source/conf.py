"""
Application configuration module.

This module provides centralized configuration management using pydantic-settings.
All configuration values are loaded from environment variables with sensible defaults.

Required environment variables:
    - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME: Database connection settings
    - ACCESS_TOKEN_SECRET, REFRESH_TOKEN_SECRET: JWT signing secrets
    - VERIFY_TOKEN: Instagram webhook verification token
    - OPENROUTER_KEY: OpenRouter API key
    - MINIO_USER, MINIO_PASSWORD: MinIO credentials

Configuration values can be set via:
    1. Environment variables (highest priority)
    2. .env file in config/ directory
    3. Default values defined in this class

For production deployments, use secure environment variables and strong secrets.
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Main application configuration.
    
    Uses pydantic-settings to load configuration from environment variables
    with fallback to .env file and class defaults.
    """
    
    model_config = SettingsConfigDict(
        env_file="config/.env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database Configuration
    db_host: str = Field(
        default="db",
        description="PostgreSQL database host"
    )
    db_port: int = Field(
        default=5432,
        description="PostgreSQL database port",
        ge=1,
        le=65535
    )
    db_user: str = Field(
        default="postgres",
        description="PostgreSQL database user"
    )
    db_password: str = Field(
        default="",
        description="PostgreSQL database password"
    )
    db_name: str = Field(
        default="instagram",
        description="PostgreSQL database name"
    )

    # JWT Configuration
    code_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_secret: str = Field(
        default="",
        description="Secret key for signing access tokens. Must be set in production!"
    )
    refresh_token_secret: str = Field(
        default="",
        description="Secret key for signing refresh tokens. Must be set in production!"
    )
    access_token_exp: int = Field(
        default=600,
        description="Access token expiration time in minutes",
        ge=1
    )
    refresh_token_exp: int = Field(
        default=30,
        description="Refresh token expiration time in days",
        ge=1
    )

    # Instagram Webhook Configuration
    verify_token: str = Field(
        default="strstrstr",
        description="Token for Instagram webhook verification"
    )

    # OpenRouter AI Configuration
    openrouter_key: str = Field(
        default="",
        description="OpenRouter API key. Required for AI features."
    )
    openrouter_model_key: str = Field(
        default="google/gemini-2.5-flash",
        description="Default OpenRouter model for text generation"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        description="OpenRouter API base URL"
    )
    openrouter_image_model_key: str = Field(
        default="google/gemini-2.5-flash-image-preview",
        description="OpenRouter model for image generation"
    )
    openrouter_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        ge=1
    )
    openrouter_max_tokens: int = Field(
        default=1500,
        description="Maximum tokens for AI responses",
        ge=1
    )
    openrouter_temperature: float = Field(
        default=0.7,
        description="AI response temperature (0.0-2.0)",
        ge=0.0,
        le=2.0
    )

    # MinIO Storage Configuration
    minio_host: str = Field(
        default="minio",
        description="MinIO server host"
    )
    minio_port: int = Field(
        default=9000,
        description="MinIO server port",
        ge=1,
        le=65535
    )
    minio_user: str = Field(
        default="admin",
        description="MinIO root user"
    )
    minio_password: str = Field(
        default="",
        description="MinIO root password"
    )
    minio_bucket: str = Field(
        default="images",
        description="MinIO bucket name for storing images"
    )
    minio_public_url: str = Field(
        default="",
        description="Public URL for accessing MinIO objects. Required for Instagram."
    )

    @property
    def db_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def db_url_sync(self) -> str:
        """Construct synchronous PostgreSQL connection URL for migrations."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @field_validator('access_token_secret', 'refresh_token_secret')
    @classmethod
    def validate_jwt_secrets(cls, v: str) -> str:
        """Warn if JWT secrets are using default/empty values."""
        if not v or v == "":
            import warnings
            warnings.warn(
                "JWT secrets are not set! This is insecure. "
                "Set ACCESS_TOKEN_SECRET and REFRESH_TOKEN_SECRET environment variables.",
                UserWarning
            )
        return v

    @field_validator('db_password')
    @classmethod
    def validate_db_password(cls, v: str) -> str:
        """Warn if database password is empty."""
        if not v:
            import warnings
            warnings.warn(
                "Database password is empty! This may not work in production.",
                UserWarning
            )
        return v


settings = Config()
