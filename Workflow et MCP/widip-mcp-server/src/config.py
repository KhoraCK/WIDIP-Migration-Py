"""
Configuration centralisée du serveur MCP WIDIP.
Utilise pydantic-settings pour charger les variables d'environnement.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# SAFEGUARD - Niveaux de sécurité L0-L4
# =============================================================================


class SecurityLevel(str, Enum):
    """
    Niveaux de sécurité SAFEGUARD pour les tools MCP.

    L0 (READ_ONLY): Lecture seule, auto-exécution autorisée
    L1 (MINOR): Actions mineures, auto si confidence > 80%
    L2 (MODERATE): Actions modérées, notification tech requise
    L3 (SENSITIVE): Actions sensibles, validation humaine OBLIGATOIRE
    L4 (FORBIDDEN): Actions interdites à l'IA, humain uniquement
    """
    L0_READ_ONLY = "L0"
    L1_MINOR = "L1"
    L2_MODERATE = "L2"
    L3_SENSITIVE = "L3"
    L4_FORBIDDEN = "L4"


# Mapping des tools vers leurs niveaux de sécurité
TOOL_SECURITY_LEVELS: dict[str, SecurityLevel] = {
    # GLPI Tools
    "glpi_search_new_tickets": SecurityLevel.L0_READ_ONLY,
    "glpi_get_ticket_details": SecurityLevel.L0_READ_ONLY,
    "glpi_search_client": SecurityLevel.L0_READ_ONLY,
    "glpi_create_ticket": SecurityLevel.L1_MINOR,
    "glpi_add_ticket_followup": SecurityLevel.L1_MINOR,
    "glpi_update_ticket_status": SecurityLevel.L2_MODERATE,
    "glpi_assign_ticket": SecurityLevel.L2_MODERATE,
    "glpi_close_ticket": SecurityLevel.L3_SENSITIVE,  # Clôturer = décision importante
    "glpi_send_email": SecurityLevel.L1_MINOR,

    # Observium Tools
    "observium_get_device_status": SecurityLevel.L0_READ_ONLY,
    "observium_get_device_metrics": SecurityLevel.L0_READ_ONLY,
    "observium_get_device_alerts": SecurityLevel.L0_READ_ONLY,
    "observium_get_device_history": SecurityLevel.L0_READ_ONLY,

    # Active Directory Tools - SENSIBLES
    "ad_check_user": SecurityLevel.L0_READ_ONLY,
    "ad_get_user_info": SecurityLevel.L0_READ_ONLY,
    "ad_unlock_account": SecurityLevel.L2_MODERATE,
    "ad_reset_password": SecurityLevel.L3_SENSITIVE,  # Reset MDP = validation humaine
    "ad_create_user": SecurityLevel.L4_FORBIDDEN,  # Création compte = INTERDIT à l'IA
    "ad_disable_account": SecurityLevel.L3_SENSITIVE,
    "ad_enable_account": SecurityLevel.L2_MODERATE,  # Réactivation compte = modéré
    "ad_move_to_ou": SecurityLevel.L2_MODERATE,  # Déplacement OU = modéré
    "ad_copy_groups_from": SecurityLevel.L3_SENSITIVE,  # Copie groupes = validation humaine

    # Memory/RAG Tools
    "memory_search_similar_cases": SecurityLevel.L0_READ_ONLY,
    "memory_add_knowledge": SecurityLevel.L1_MINOR,
    "memory_get_stats": SecurityLevel.L0_READ_ONLY,  # Stats de la base de connaissances

    # MySecret Tools
    "mysecret_create_secret": SecurityLevel.L1_MINOR,

    # Notification Tools
    "notify_client": SecurityLevel.L1_MINOR,  # Envoi email client = informatif
    "notify_technician": SecurityLevel.L1_MINOR,  # Alerte technicien = informatif
    "request_human_validation": SecurityLevel.L1_MINOR,  # Demande de validation = informatif

    # Enrichisseur Tools (Cercle Vertueux)
    "glpi_get_resolved_tickets": SecurityLevel.L0_READ_ONLY,  # Lecture tickets résolus
    "memory_check_exists": SecurityLevel.L0_READ_ONLY,  # Vérification existence dans RAG
    "enrichisseur_extract_knowledge": SecurityLevel.L0_READ_ONLY,  # Extraction connaissances
    "enrichisseur_get_stats": SecurityLevel.L0_READ_ONLY,  # Stats RAG
    "enrichisseur_run_batch": SecurityLevel.L1_MINOR,  # Batch enrichissement (écriture RAG)
}


class Settings(BaseSettings):
    """Configuration globale du serveur MCP."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Server Configuration
    # -------------------------------------------------------------------------
    mcp_server_host: str = Field(default="0.0.0.0", description="Host du serveur")
    mcp_server_port: int = Field(default=3001, description="Port du serveur")
    mcp_server_debug: bool = Field(default=False, description="Mode debug")
    log_level: str = Field(default="INFO", description="Niveau de log")
    environment: str = Field(
        default="development",
        description="Environnement d'exécution (development, staging, production)"
    )

    # -------------------------------------------------------------------------
    # Security Configuration (SAFEGUARD)
    # -------------------------------------------------------------------------
    mcp_api_key: SecretStr = Field(
        default="",
        description="Clé API pour authentifier les requêtes MCP (OBLIGATOIRE en production)"
    )
    mcp_require_auth: bool = Field(
        default=True,
        description="Exiger l'authentification API Key"
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:5678,http://n8n:5678,http://127.0.0.1:5678",
        description="Origins autorisées pour CORS (séparées par des virgules)"
    )
    safeguard_enabled: bool = Field(
        default=True,
        description="Activer les niveaux de sécurité SAFEGUARD L0-L4"
    )

    def validate_security(self) -> list[str]:
        """
        Valide la configuration de sécurité.
        Retourne une liste d'erreurs critiques si la config est dangereuse.
        """
        errors = []

        # =============================================================================
        # PRODUCTION: Sécurité STRICTE obligatoire
        # =============================================================================
        if self.environment.lower() == "production":
            # 1. Authentification OBLIGATOIRE en production
            if not self.mcp_require_auth:
                errors.append(
                    "CRITICAL: MCP_REQUIRE_AUTH must be 'true' in production. "
                    "Running without authentication is a major security risk."
                )

            # 2. API Key OBLIGATOIRE en production
            if not self.mcp_api_key.get_secret_value():
                errors.append(
                    "CRITICAL: MCP_API_KEY is empty in production. "
                    "Set a strong API key (32+ chars) to secure the MCP server."
                )

            # 3. SAFEGUARD OBLIGATOIRE en production
            if not self.safeguard_enabled:
                errors.append(
                    "CRITICAL: SAFEGUARD_ENABLED must be 'true' in production. "
                    "SAFEGUARD L0-L4 security levels are essential."
                )

            # 4. CORS doit être configuré (pas de fallback localhost)
            if not self.cors_allowed_origins or self.cors_allowed_origins == "":
                errors.append(
                    "CRITICAL: CORS_ALLOWED_ORIGINS must be configured in production. "
                    "Specify exact origins (no wildcards)."
                )

            # 5. Clé de chiffrement Redis OBLIGATOIRE pour SAFEGUARD L3
            if not self.redis_secret_key.get_secret_value():
                errors.append(
                    "CRITICAL: REDIS_SECRET_KEY is empty in production. "
                    "Required for encrypting L3 approval secrets. Generate with: "
                    "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )

        # =============================================================================
        # TOUS ENVIRONNEMENTS: Validations générales
        # =============================================================================

        # API Key obligatoire si auth requise
        if self.mcp_require_auth and not self.mcp_api_key.get_secret_value():
            errors.append(
                "CRITICAL: mcp_require_auth=True mais MCP_API_KEY est vide. "
                "Définissez MCP_API_KEY ou mettez MCP_REQUIRE_AUTH=False (dev uniquement)."
            )

        # API Key trop courte
        api_key = self.mcp_api_key.get_secret_value()
        if api_key and len(api_key) < 32:
            errors.append(
                f"WARNING: MCP_API_KEY trop courte ({len(api_key)} chars). "
                "Utilisez au moins 32 caractères pour la production."
            )

        # Clé de chiffrement Redis trop courte
        redis_key = self.redis_secret_key.get_secret_value()
        if redis_key and len(redis_key) < 32:
            errors.append(
                f"WARNING: REDIS_SECRET_KEY trop courte ({len(redis_key)} chars). "
                "Utilisez au moins 32 caractères (Fernet AES-128 recommandé)."
            )

        return errors

    # -------------------------------------------------------------------------
    # GLPI API Configuration
    # -------------------------------------------------------------------------
    glpi_url: str = Field(default="", description="URL de l'API GLPI")
    glpi_app_token: SecretStr = Field(default="", description="App-Token GLPI")
    glpi_user_token: SecretStr = Field(default="", description="User-Token GLPI")

    # -------------------------------------------------------------------------
    # Observium API Configuration
    # -------------------------------------------------------------------------
    observium_url: str = Field(default="", description="URL de l'API Observium")
    observium_user: str = Field(default="", description="Utilisateur API Observium")
    observium_pass: SecretStr = Field(default="", description="Mot de passe API Observium")

    # -------------------------------------------------------------------------
    # Active Directory / LDAP Configuration
    # -------------------------------------------------------------------------
    ldap_server: str = Field(default="", description="Serveur LDAP (ldap://host:389)")
    ldap_use_ssl: bool = Field(default=False, description="Utiliser LDAPS (port 636)")
    ldap_verify_ssl: bool = Field(
        default=True,
        description="Vérifier le certificat SSL du serveur LDAPS (RECOMMANDÉ en production)"
    )
    ldap_ca_cert_path: str = Field(
        default="",
        description="Chemin vers le certificat CA pour LDAPS (optionnel si CA système)"
    )
    ldap_base_dn: str = Field(default="", description="Base DN")
    ldap_bind_user: str = Field(default="", description="DN du compte de service")
    ldap_bind_pass: SecretStr = Field(default="", description="Mot de passe du compte")
    ldap_user_search_base: str = Field(default="", description="Base de recherche utilisateurs")

    # -------------------------------------------------------------------------
    # SMTP Configuration
    # -------------------------------------------------------------------------
    smtp_host: str = Field(default="", description="Serveur SMTP")
    smtp_port: int = Field(default=587, description="Port SMTP")
    smtp_use_tls: bool = Field(default=True, description="Utiliser TLS")
    smtp_user: str = Field(default="", description="Utilisateur SMTP")
    smtp_pass: SecretStr = Field(default="", description="Mot de passe SMTP")
    smtp_from_name: str = Field(default="WIDIP", description="Nom expéditeur")
    smtp_from_email: str = Field(default="", description="Email expéditeur")

    # -------------------------------------------------------------------------
    # MySecret API Configuration
    # -------------------------------------------------------------------------
    mysecret_url: str = Field(default="", description="URL de l'API MySecret")
    mysecret_api_key: SecretStr = Field(default="", description="Clé API MySecret")

    # -------------------------------------------------------------------------
    # Notification Webhooks (Teams/Slack)
    # -------------------------------------------------------------------------
    teams_webhook_url: str = Field(default="", description="URL du webhook Microsoft Teams")
    slack_webhook_url: str = Field(default="", description="URL du webhook Slack")
    glpi_ticket_base_url: str = Field(
        default="",
        description="URL de base pour les liens vers tickets GLPI (ex: https://glpi.example.com/front/ticket.form.php?id=)"
    )
    safeguard_dashboard_url: str = Field(
        default="",
        description="URL du Dashboard SAFEGUARD pour les validations humaines"
    )

    # -------------------------------------------------------------------------
    # PostgreSQL Configuration
    # -------------------------------------------------------------------------
    postgres_host: str = Field(default="postgres", description="Host PostgreSQL")
    postgres_port: int = Field(default=5432, description="Port PostgreSQL")
    postgres_user: str = Field(default="postgres", description="Utilisateur PostgreSQL")
    postgres_pass: SecretStr = Field(default="", description="Mot de passe PostgreSQL")
    postgres_db: str = Field(default="widip_knowledge", description="Base de données")

    # -------------------------------------------------------------------------
    # Redis Configuration
    # -------------------------------------------------------------------------
    redis_host: str = Field(default="redis", description="Host Redis")
    redis_port: int = Field(default=6379, description="Port Redis")
    redis_password: Optional[SecretStr] = Field(default=None, description="Mot de passe Redis")
    redis_db: int = Field(default=0, description="Base Redis")
    redis_secret_key: SecretStr = Field(
        default="",
        description="Clé de chiffrement pour les secrets temporaires dans Redis (32+ chars). "
                    "OBLIGATOIRE en production pour la persistance des secrets SAFEGUARD."
    )

    # -------------------------------------------------------------------------
    # Ollama Configuration (Embeddings)
    # -------------------------------------------------------------------------
    ollama_url: str = Field(default="http://localhost:11434", description="URL Ollama")
    ollama_embed_model: str = Field(
        default="intfloat/multilingual-e5-large",
        description="Modèle embeddings (e5-multilingual-large = 1024 dim)"
    )
    ollama_embed_dimensions: int = Field(
        default=1024,
        description="Dimensions des embeddings (e5-multilingual-large = 1024)"
    )

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @property
    def postgres_dsn(self) -> str:
        """Retourne le DSN PostgreSQL."""
        password = self.postgres_pass.get_secret_value() if self.postgres_pass else ""
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Retourne l'URL Redis."""
        if self.redis_password:
            password = self.redis_password.get_secret_value()
            return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance singleton des settings."""
    return Settings()


# Alias pour import simplifié
settings = get_settings()
