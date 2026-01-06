"""
Tools MCP pour MySecret.

Ce module expose les outils de partage sécurisé aux agents IA:
- Création de liens secrets avec expiration
"""

from typing import Any

from ..clients.mysecret import mysecret_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
)


@tool_registry.register_function(
    name="mysecret_create_secret",
    description="""Crée un lien de partage sécurisé pour un contenu sensible (ex: mot de passe).
Le lien expire automatiquement après un certain temps ou nombre de vues.
Utilise ce tool après un reset de mot de passe pour transmettre le nouveau
mot de passe de façon sécurisée au technicien ou à l'utilisateur.""",
    parameters={
        "payload": string_param(
            "Contenu secret à partager (ex: mot de passe temporaire)",
            required=True,
        ),
        "expire_days": int_param(
            "Nombre de jours avant expiration du lien",
            required=False,
            default=7,
        ),
        "expire_views": int_param(
            "Nombre de vues maximum avant expiration",
            required=False,
            default=5,
        ),
    },
)
async def mysecret_create_secret(
    payload: str,
    expire_days: int = 7,
    expire_views: int = 5,
) -> dict[str, Any]:
    """Crée un lien secret sécurisé."""
    result = await mysecret_client.create_secret(
        payload=payload,
        expire_days=expire_days,
        expire_views=expire_views,
    )
    result["operation"] = "create_secret"
    return result
