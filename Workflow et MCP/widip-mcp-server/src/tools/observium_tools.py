"""
Tools MCP pour Observium.

Ce module expose les outils de monitoring réseau Observium aux agents IA:
- État des devices (up/down)
- Métriques (ports, bande passante)
- Alertes actives
- Historique des incidents
"""

from typing import Any

from ..clients.observium import observium_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
)


@tool_registry.register_function(
    name="observium_get_device_status",
    description="""Récupère l'état complet d'un équipement réseau dans Observium.
Utilise ce tool pour vérifier si un device est up/down, son uptime, localisation, etc.
Retourne: statut, uptime, IP, hardware, OS, dernière interrogation.""",
    parameters={
        "device_name": string_param(
            "Nom ou hostname du device (ex: SW-EHPAD-BELLEVUE)",
            required=True,
        ),
    },
)
async def observium_get_device_status(device_name: str) -> dict[str, Any]:
    """Récupère le statut d'un device Observium."""
    return await observium_client.get_device_status(device_name)


@tool_registry.register_function(
    name="observium_get_device_metrics",
    description="""Récupère les métriques détaillées d'un équipement réseau.
Utilise ce tool pour obtenir les infos sur les ports (up/down/erreurs),
la bande passante utilisée, et l'état de santé général.
Utile pour diagnostiquer des problèmes de performance réseau.""",
    parameters={
        "device_name": string_param(
            "Nom ou hostname du device",
            required=True,
        ),
    },
)
async def observium_get_device_metrics(device_name: str) -> dict[str, Any]:
    """Récupère les métriques d'un device."""
    return await observium_client.get_device_metrics(device_name)


@tool_registry.register_function(
    name="observium_get_device_alerts",
    description="""Récupère les alertes actives d'un équipement réseau.
Utilise ce tool pour voir les alertes en cours sur un device:
type d'alerte, sévérité, timestamp, durée.
Permet d'identifier rapidement les problèmes actifs.""",
    parameters={
        "device_name": string_param(
            "Nom ou hostname du device",
            required=True,
        ),
    },
)
async def observium_get_device_alerts(device_name: str) -> dict[str, Any]:
    """Récupère les alertes d'un device."""
    return await observium_client.get_device_alerts(device_name)


@tool_registry.register_function(
    name="observium_get_device_history",
    description="""Récupère l'historique des incidents d'un équipement réseau.
Utilise ce tool pour analyser la stabilité d'un device sur une période:
- Nombre d'incidents down/up
- Temps de downtime total
- Pourcentage d'uptime
- Recommandations de stabilité

Utile pour décider si un équipement nécessite une intervention.""",
    parameters={
        "device_name": string_param(
            "Nom ou hostname du device",
            required=True,
        ),
        "hours": int_param(
            "Nombre d'heures à analyser (historique)",
            required=False,
            default=24,
        ),
    },
)
async def observium_get_device_history(
    device_name: str,
    hours: int = 24,
) -> dict[str, Any]:
    """Récupère l'historique des incidents d'un device."""
    return await observium_client.get_device_history(device_name, hours=hours)
