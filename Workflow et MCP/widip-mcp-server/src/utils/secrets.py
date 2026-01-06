"""
Utilitaire de gestion sécurisée des secrets.

Ce module fournit des fonctions pour:
- Redacter les champs sensibles avant stockage en base
- Chiffrer/déchiffrer des secrets avec Fernet (AES-128-CBC)
- Stocker temporairement des secrets chiffrés dans Redis

IMPORTANT: Ne JAMAIS stocker de mots de passe en clair dans PostgreSQL!
"""

import base64
import hashlib
import json
import secrets as stdlib_secrets
from datetime import timedelta
from typing import Any, Optional

import structlog

# Liste des noms de champs considérés comme sensibles
SENSITIVE_FIELD_NAMES = frozenset([
    "password",
    "new_password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credentials",
    "auth",
    "authorization",
    "_temp_password",
])

# Valeur de remplacement pour les champs redactés
REDACTED_VALUE = "[REDACTED]"

logger = structlog.get_logger(__name__)


def redact_sensitive_fields(
    data: dict[str, Any],
    sensitive_fields: Optional[frozenset[str]] = None,
) -> dict[str, Any]:
    """
    Redacte les champs sensibles d'un dictionnaire.

    Args:
        data: Dictionnaire à nettoyer
        sensitive_fields: Liste des noms de champs sensibles (optionnel)

    Returns:
        Copie du dictionnaire avec les valeurs sensibles remplacées par [REDACTED]

    Example:
        >>> redact_sensitive_fields({"username": "john", "password": "secret123"})
        {"username": "john", "password": "[REDACTED]"}
    """
    if not data:
        return data

    fields = sensitive_fields or SENSITIVE_FIELD_NAMES
    redacted = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Vérifier si c'est un champ sensible
        if key_lower in fields or any(f in key_lower for f in fields):
            redacted[key] = REDACTED_VALUE
        elif isinstance(value, dict):
            # Récursion pour les objets imbriqués
            redacted[key] = redact_sensitive_fields(value, fields)
        elif isinstance(value, list):
            # Traiter les listes
            redacted[key] = [
                redact_sensitive_fields(item, fields)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            redacted[key] = value

    return redacted


def has_sensitive_fields(data: dict[str, Any]) -> bool:
    """
    Vérifie si un dictionnaire contient des champs sensibles.

    Args:
        data: Dictionnaire à vérifier

    Returns:
        True si des champs sensibles sont présents
    """
    if not data:
        return False

    for key, value in data.items():
        key_lower = key.lower()

        if key_lower in SENSITIVE_FIELD_NAMES or any(f in key_lower for f in SENSITIVE_FIELD_NAMES):
            return True

        if isinstance(value, dict) and has_sensitive_fields(value):
            return True

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and has_sensitive_fields(item):
                    return True

    return False


def extract_sensitive_fields(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extrait les champs sensibles d'un dictionnaire.

    Args:
        data: Dictionnaire source

    Returns:
        Tuple (données_nettoyées, secrets_extraits)

    Example:
        >>> clean, secrets = extract_sensitive_fields({"user": "john", "password": "secret"})
        >>> clean
        {"user": "john", "password": "[REDACTED]"}
        >>> secrets
        {"password": "secret"}
    """
    if not data:
        return data, {}

    cleaned = {}
    secrets_found = {}

    for key, value in data.items():
        key_lower = key.lower()

        if key_lower in SENSITIVE_FIELD_NAMES or any(f in key_lower for f in SENSITIVE_FIELD_NAMES):
            cleaned[key] = REDACTED_VALUE
            secrets_found[key] = value
        elif isinstance(value, dict):
            nested_clean, nested_secrets = extract_sensitive_fields(value)
            cleaned[key] = nested_clean
            if nested_secrets:
                secrets_found[key] = nested_secrets
        else:
            cleaned[key] = value

    return cleaned, secrets_found


class SecureSecretStore:
    """
    Stockage sécurisé des secrets dans Redis avec chiffrement.

    Utilise Fernet (AES-128-CBC) pour le chiffrement at-rest.
    Les secrets sont stockés avec un TTL automatique.
    """

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        """
        Initialise le store de secrets.

        Args:
            encryption_key: Clé de chiffrement (32 bytes base64).
                           Si non fournie, générée aléatoirement (non persistante!).
        """
        self._redis_client = None

        if encryption_key:
            # Dériver une clé Fernet depuis la clé fournie
            key_bytes = hashlib.sha256(encryption_key.encode()).digest()
            self._fernet_key = base64.urlsafe_b64encode(key_bytes)
        else:
            # Générer une clé aléatoire (WARNING: perdue au redémarrage!)
            self._fernet_key = base64.urlsafe_b64encode(stdlib_secrets.token_bytes(32))
            logger.warning(
                "secret_store_ephemeral_key",
                warning="Using ephemeral encryption key. Secrets will be lost on restart. "
                        "Set REDIS_SECRET_KEY in production."
            )

    async def _get_redis(self):
        """Retourne le client Redis."""
        if self._redis_client is None:
            import redis.asyncio as aioredis
            from ..config import settings

            self._redis_client = aioredis.from_url(
                settings.redis_url,
                decode_responses=False,  # Garder les bytes pour le chiffrement
            )
        return self._redis_client

    def _encrypt(self, data: Any) -> bytes:
        """Chiffre des données avec Fernet."""
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logger.error("cryptography_not_installed")
            raise ImportError(
                "Le package 'cryptography' est requis. "
                "Installez-le avec: pip install cryptography"
            )

        fernet = Fernet(self._fernet_key)
        json_data = json.dumps(data).encode("utf-8")
        return fernet.encrypt(json_data)

    def _decrypt(self, encrypted: bytes) -> Any:
        """Déchiffre des données avec Fernet."""
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            raise ImportError("Le package 'cryptography' est requis.")

        fernet = Fernet(self._fernet_key)
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))

    async def store_secret(
        self,
        key: str,
        data: Any,
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Stocke un secret chiffré dans Redis.

        Args:
            key: Identifiant unique du secret
            data: Données à stocker
            ttl_seconds: Durée de vie en secondes

        Returns:
            Clé de stockage
        """
        redis = await self._get_redis()
        redis_key = f"widip:secret:{key}"
        encrypted = self._encrypt(data)

        await redis.setex(
            redis_key,
            timedelta(seconds=ttl_seconds),
            encrypted,
        )

        logger.info("secret_stored", key=key[:20] + "...", ttl=ttl_seconds)
        return key

    async def get_secret(self, key: str) -> Optional[Any]:
        """
        Récupère un secret depuis Redis.

        Args:
            key: Identifiant du secret

        Returns:
            Données déchiffrées ou None si non trouvé/expiré
        """
        redis = await self._get_redis()
        redis_key = f"widip:secret:{key}"

        encrypted = await redis.get(redis_key)

        if encrypted is None:
            logger.warning("secret_not_found", key=key[:20] + "...")
            return None

        try:
            return self._decrypt(encrypted)
        except Exception as e:
            logger.error("secret_decrypt_error", key=key[:20] + "...", error=str(e))
            return None

    async def delete_secret(self, key: str) -> bool:
        """
        Supprime un secret de Redis.

        Args:
            key: Identifiant du secret

        Returns:
            True si supprimé, False si non trouvé
        """
        redis = await self._get_redis()
        redis_key = f"widip:secret:{key}"

        result = await redis.delete(redis_key)
        return result > 0

    async def close(self) -> None:
        """Ferme la connexion Redis."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None


def get_secret_store() -> SecureSecretStore:
    """
    Factory pour créer le SecureSecretStore avec la clé de config.

    Utilise REDIS_SECRET_KEY si configuré, sinon génère une clé éphémère.
    """
    from ..config import settings

    key = settings.redis_secret_key.get_secret_value() if settings.redis_secret_key else None
    return SecureSecretStore(encryption_key=key if key else None)


# Instance singleton (utilise REDIS_SECRET_KEY de la config si disponible)
secret_store = get_secret_store()
