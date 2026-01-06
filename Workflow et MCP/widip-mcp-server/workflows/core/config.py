"""
Configuration for WIDIP workflows
"""

from functools import lru_cache
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class WorkflowSettings(BaseSettings):
    """
    Workflow configuration loaded from environment variables.
    """

    # ==================== General ====================
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"  # 'json' or 'console'

    # ==================== MCP Server ====================
    mcp_server_url: str = "http://localhost:3001"
    mcp_api_key: Optional[SecretStr] = None
    mcp_timeout_seconds: int = 30
    mcp_max_retries: int = 3

    # ==================== Redis ====================
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0

    # ==================== PostgreSQL ====================
    database_url: Optional[str] = None

    # ==================== Scheduler ====================
    scheduler_enabled: bool = True

    # Health Check
    health_check_interval_seconds: int = 30
    health_check_timeout_ms: int = 5000

    # Support
    support_polling_interval_minutes: int = 3

    # Enrichisseur
    enrichisseur_hour: int = 18
    enrichisseur_minute: int = 0

    # ==================== GLPI ====================
    glpi_url: Optional[str] = None
    glpi_app_token: Optional[SecretStr] = None
    glpi_user_token: Optional[SecretStr] = None

    # ==================== Notifications ====================
    slack_webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[SecretStr] = None
    notification_email_from: Optional[str] = None

    # ==================== Ollama ====================
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"

    class Config:
        env_prefix = "WIDIP_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_mcp_api_key(self) -> Optional[str]:
        """Get MCP API key as string"""
        if self.mcp_api_key:
            return self.mcp_api_key.get_secret_value()
        return None


@lru_cache()
def get_settings() -> WorkflowSettings:
    """Get cached settings instance"""
    return WorkflowSettings()


# Convenience access
settings = get_settings()
