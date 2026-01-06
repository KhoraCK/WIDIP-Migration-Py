"""
Client HTTP de base pour les appels API.

Fournit une abstraction commune pour tous les clients API avec:
- Gestion des sessions HTTP
- Retry automatique
- Logging structuré
- Gestion des erreurs
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
import structlog

from ..utils.retry import with_retry

logger = structlog.get_logger(__name__)


class APIError(Exception):
    """Erreur lors d'un appel API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(APIError):
    """Erreur d'authentification API."""

    pass


class NotFoundError(APIError):
    """Ressource non trouvée."""

    pass


class RateLimitError(APIError):
    """Limite de requêtes atteinte."""

    pass


class BaseClient(ABC):
    """
    Client HTTP de base abstrait.

    Tous les clients API héritent de cette classe.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialise le client.

        Args:
            base_url: URL de base de l'API
            timeout: Timeout des requêtes en secondes
            max_retries: Nombre de retries sur erreur
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Retourne les headers d'authentification."""
        pass

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Gère les erreurs HTTP.

        Args:
            response: Réponse HTTP

        Raises:
            AuthenticationError: Si 401/403
            NotFoundError: Si 404
            RateLimitError: Si 429
            APIError: Pour les autres erreurs
        """
        if response.is_success:
            return

        status = response.status_code
        body = response.text[:500] if response.text else ""

        if status == 401 or status == 403:
            raise AuthenticationError(
                f"Authentication failed: {status}",
                status_code=status,
                response_body=body,
            )
        elif status == 404:
            raise NotFoundError(
                f"Resource not found: {response.url}",
                status_code=status,
                response_body=body,
            )
        elif status == 429:
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=status,
                response_body=body,
            )
        else:
            raise APIError(
                f"API error {status}: {body}",
                status_code=status,
                response_body=body,
            )

    @with_retry(max_attempts=3)
    async def _get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Effectue une requête GET.

        Args:
            endpoint: Endpoint relatif
            params: Paramètres de requête

        Returns:
            Réponse JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug("http_get", url=url, params=params)

        response = await self.client.get(
            url,
            params=params,
            headers=self._get_headers(),
        )

        self._handle_error(response)
        return response.json()

    @with_retry(max_attempts=3)
    async def _post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Effectue une requête POST.

        Args:
            endpoint: Endpoint relatif
            data: Données form-encoded
            json_data: Données JSON

        Returns:
            Réponse JSON
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug("http_post", url=url)

        response = await self.client.post(
            url,
            data=data,
            json=json_data,
            headers=self._get_headers(),
        )

        self._handle_error(response)

        # Certaines APIs retournent du vide sur succès
        if not response.text:
            return {"success": True}

        return response.json()

    @with_retry(max_attempts=3)
    async def _put(
        self,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Effectue une requête PUT."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug("http_put", url=url)

        response = await self.client.put(
            url,
            json=json_data,
            headers=self._get_headers(),
        )

        self._handle_error(response)
        return response.json() if response.text else {"success": True}

    @with_retry(max_attempts=3)
    async def _delete(self, endpoint: str) -> Any:
        """Effectue une requête DELETE."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug("http_delete", url=url)

        response = await self.client.delete(
            url,
            headers=self._get_headers(),
        )

        self._handle_error(response)
        return response.json() if response.text else {"success": True}

    async def __aenter__(self) -> "BaseClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()
