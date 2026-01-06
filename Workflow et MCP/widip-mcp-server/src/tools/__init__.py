"""
Tools MCP pour WIDIP.

Ce module regroupe tous les tools disponibles via le serveur MCP.
L'import de ce module enregistre automatiquement tous les tools dans le registre.
"""

# Import des modules de tools pour enregistrement automatique
from . import glpi_tools
from . import observium_tools
from . import ad_tools
from . import mysecret_tools
from . import memory_tools
from . import notification_tools
from . import enrichisseur_tools

__all__ = [
    "glpi_tools",
    "observium_tools",
    "ad_tools",
    "mysecret_tools",
    "memory_tools",
    "notification_tools",
    "enrichisseur_tools",
]
