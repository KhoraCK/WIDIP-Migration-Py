"""
Client pour MySecret API.

MySecret est un service de partage sécurisé de secrets (type PasswordPusher).
Utilisé pour transmettre des mots de passe temporaires de façon sécurisée.
"""

from typing import Any

import structlog

from ..config import settings
from .base import BaseClient

logger = structlog.get_logger(__name__)


class MySecretClient(BaseClient):
    """
    Client pour l'API MySecret (PasswordPusher).

    Permet de créer des liens de partage sécurisé avec expiration.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.mysecret_url,
            timeout=30.0,
        )

    def _get_headers(self) -> dict[str, str]:
        """Retourne les headers pour MySecret."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        # Ajouter l'API key si configurée
        api_key = settings.mysecret_api_key.get_secret_value()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def create_secret(
        self,
        payload: str,
        expire_days: int = 7,
        expire_views: int = 5,
    ) -> dict[str, Any]:
        """
        Crée un lien secret avec expiration.

        Args:
            payload: Le contenu secret à partager (ex: mot de passe)
            expire_days: Nombre de jours avant expiration
            expire_views: Nombre de vues avant expiration

        Returns:
            URL du secret et métadonnées
        """
        logger.info("mysecret_create", expire_days=expire_days, expire_views=expire_views)

        try:
            # Format form-urlencoded comme dans le workflow N8N
            response = await self.client.post(
                f"{self.base_url}/p.json",
                data={
                    "password[payload]": payload,
                    "password[expire_after_days]": str(expire_days),
                    "password[expire_after_views]": str(expire_views),
                },
                headers=self._get_headers(),
            )

            if not response.is_success:
                error_msg = response.text[:200] if response.text else "Unknown error"
                logger.error("mysecret_create_failed", error=error_msg)
                return {"success": False, "error": error_msg}

            data = response.json()

            if not data.get("url_token"):
                return {"success": False, "error": "No url_token in response"}

            # Construire l'URL complète
            base_url = self.base_url.rstrip("/")
            secret_url = f"{base_url}/p/{data['url_token']}"

            logger.info("mysecret_created", url_token=data["url_token"][:8] + "...")

            return {
                "success": True,
                "secret_url": secret_url,
                "expires_in_days": data.get("expire_after_days", expire_days),
                "expires_after_views": data.get("expire_after_views", expire_views),
                "message": "Lien secret créé avec succès",
            }

        except Exception as e:
            logger.exception("mysecret_create_error", error=str(e))
            return {"success": False, "error": str(e)}


# Instance singleton
mysecret_client = MySecretClient()
