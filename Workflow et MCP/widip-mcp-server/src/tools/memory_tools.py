"""
Tools MCP pour la mémoire RAG.

Ce module expose les outils de mémoire à long terme aux agents IA:
- Recherche de cas similaires dans la base de connaissances
- Ajout de nouvelles procédures extraites des tickets résolus
"""

from typing import Any, Optional

from ..clients.memory import memory_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
    array_param,
)


@tool_registry.register_function(
    name="memory_search_similar_cases",
    description="""Recherche des cas similaires dans la base de connaissances WIDIP.
Utilise ce tool AVANT de résoudre un problème pour voir si une solution existe déjà.
Retourne les tickets passés similaires avec leur problème et solution.
Très utile pour les diagnostics et résolutions de tickets.""",
    parameters={
        "query": string_param(
            "Description du problème à rechercher (ex: 'VPN ne fonctionne plus EHPAD Bellevue')",
            required=True,
        ),
        "limit": int_param(
            "Nombre maximum de résultats à retourner",
            required=False,
            default=3,
        ),
    },
)
async def memory_search_similar_cases(
    query: str,
    limit: int = 3,
) -> dict[str, Any]:
    """Recherche des cas similaires dans la mémoire."""
    result = await memory_client.search_similar_cases(query=query, limit=limit)
    result["operation"] = "search_similar_cases"
    return result


@tool_registry.register_function(
    name="memory_add_knowledge",
    description="""Ajoute une nouvelle connaissance à la base WIDIP.
Utilise ce tool pour enrichir la base avec un nouveau cas résolu.
Le système apprendra de ce cas pour les futures recherches.
Typiquement appelé par l'agent ENRICHISSEUR après résolution d'un ticket.""",
    parameters={
        "ticket_id": string_param(
            "ID du ticket GLPI source",
            required=True,
        ),
        "problem_summary": string_param(
            "Résumé du problème rencontré",
            required=True,
        ),
        "solution_summary": string_param(
            "Résumé de la solution appliquée",
            required=True,
        ),
        "category": string_param(
            "Catégorie du problème (ex: VPN, Imprimante, AD, etc.)",
            required=False,
        ),
        "tags": array_param(
            "Tags pour faciliter la recherche",
            required=False,
        ),
    },
)
async def memory_add_knowledge(
    ticket_id: str,
    problem_summary: str,
    solution_summary: str,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Ajoute une connaissance à la base."""
    result = await memory_client.add_knowledge(
        ticket_id=ticket_id,
        problem_summary=problem_summary,
        solution_summary=solution_summary,
        category=category,
        tags=tags,
    )
    result["operation"] = "add_knowledge"
    return result


@tool_registry.register_function(
    name="memory_get_stats",
    description="""Récupère les statistiques de la base de connaissances.
Retourne le nombre total d'entrées, les catégories, et les dates.""",
    parameters={},
)
async def memory_get_stats() -> dict[str, Any]:
    """Récupère les stats de la mémoire."""
    result = await memory_client.get_stats()
    result["operation"] = "get_stats"
    return result
