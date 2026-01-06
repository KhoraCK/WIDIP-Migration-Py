"""
Configuration du logging structuré avec structlog.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    Configure le logging structuré pour l'application.

    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        json_format: Si True, logs en JSON (production). Sinon, logs lisibles (dev)
    """
    # Configurer le niveau de log
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Processors communs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if json_format:
        # Format JSON pour production (compatible ELK, Loki, etc.)
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Format lisible pour développement
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configurer structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configurer aussi le logging standard (pour les libs tierces)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Réduire le bruit des libs tierces
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """Récupère un logger structlog."""
    return structlog.get_logger(name)
