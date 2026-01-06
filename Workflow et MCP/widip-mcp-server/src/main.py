"""
Point d'entrée du serveur MCP WIDIP.

Ce module initialise et démarre le serveur FastAPI MCP.
"""

import sys

import structlog
import uvicorn

from .config import settings
from .utils.logging import setup_logging

# Configurer le logging
setup_logging(settings.log_level)
logger = structlog.get_logger(__name__)


def main() -> None:
    """Point d'entrée principal."""
    # Import des tools pour enregistrement automatique
    # Cet import déclenche l'enregistrement de tous les tools dans le registre
    from . import tools  # noqa: F401
    from .mcp.server import create_mcp_app
    from .mcp.registry import tool_registry

    logger.info(
        "starting_mcp_server",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        debug=settings.mcp_server_debug,
        tools_count=len(tool_registry),
    )

    # Lister les tools disponibles
    for tool_name in sorted(tool_registry._tools.keys()):
        logger.debug("tool_available", name=tool_name)

    # Créer l'application
    app = create_mcp_app()

    # Démarrer le serveur
    uvicorn.run(
        app,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        log_level=settings.log_level.lower(),
        access_log=settings.mcp_server_debug,
    )


if __name__ == "__main__":
    main()
