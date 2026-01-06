"""
Tools MCP pour l'agent ENRICHISSEUR.

Ce module fournit les outils nécessaires au cercle vertueux d'apprentissage:
- Récupération des tickets résolus depuis GLPI
- Extraction et structuration des connaissances
- Vérification des doublons dans le RAG
- Injection dans la base de connaissances

Workflow quotidien (18h00):
1. glpi_get_resolved_tickets → Tickets résolus des 24h
2. Pour chaque ticket:
   a. memory_check_exists → Vérifier si déjà dans RAG
   b. enrichisseur_extract_knowledge → Extraire problème/solution
   c. memory_add_knowledge → Injecter dans RAG
3. enrichisseur_get_stats → Rapport d'enrichissement
"""

from typing import Any, Optional
from datetime import datetime

from ..clients.glpi import glpi_client
from ..clients.memory import memory_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
    bool_param,
)

import structlog

logger = structlog.get_logger(__name__)


@tool_registry.register_function(
    name="glpi_get_resolved_tickets",
    description="""Récupère les tickets résolus/clôturés récemment pour enrichissement RAG.
Utilisé par l'agent ENRICHISSEUR pour le cercle vertueux d'apprentissage.
Retourne les tickets avec leur description, solution et followups.
SAFEGUARD: L0 (READ_ONLY)""",
    parameters={
        "hours_since": int_param(
            "Récupérer les tickets résolus des X dernières heures",
            required=False,
            default=24,
        ),
        "limit": int_param(
            "Nombre maximum de tickets à retourner",
            required=False,
            default=50,
        ),
    },
)
async def glpi_get_resolved_tickets(
    hours_since: int = 24,
    limit: int = 50,
) -> dict[str, Any]:
    """Récupère les tickets résolus pour enrichissement."""
    result = await glpi_client.get_resolved_tickets(
        hours_since=hours_since,
        limit=limit,
    )
    result["operation"] = "get_resolved_tickets"
    return result


@tool_registry.register_function(
    name="memory_check_exists",
    description="""Vérifie si un ticket est déjà présent dans la base de connaissances RAG.
Utilisé pour éviter les doublons lors de l'enrichissement.
SAFEGUARD: L0 (READ_ONLY)""",
    parameters={
        "ticket_id": string_param(
            "ID du ticket GLPI à vérifier",
            required=True,
        ),
    },
)
async def memory_check_exists(ticket_id: str) -> dict[str, Any]:
    """Vérifie si un ticket existe déjà dans le RAG."""
    try:
        pool = await memory_client._get_pool()

        row = await pool.fetchrow(
            "SELECT id, created_at, updated_at FROM widip_knowledge_base WHERE ticket_id = $1",
            ticket_id,
        )

        if row:
            return {
                "exists": True,
                "ticket_id": ticket_id,
                "knowledge_id": row["id"],
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
            }

        return {
            "exists": False,
            "ticket_id": ticket_id,
        }

    except Exception as e:
        logger.exception("memory_check_exists_error", error=str(e))
        return {"exists": False, "error": str(e)}


@tool_registry.register_function(
    name="enrichisseur_extract_knowledge",
    description="""Extrait et structure les connaissances d'un ticket résolu.
Analyse le ticket pour en extraire:
- Un résumé du problème (problem_summary)
- Un résumé de la solution (solution_summary)
- Une catégorie
- Des tags pertinents

Cette extraction peut être affinée par un LLM pour une meilleure qualité.
SAFEGUARD: L0 (READ_ONLY) - Analyse sans modification""",
    parameters={
        "ticket_id": string_param(
            "ID du ticket",
            required=True,
        ),
        "title": string_param(
            "Titre du ticket",
            required=True,
        ),
        "description": string_param(
            "Description/contenu du ticket",
            required=True,
        ),
        "solution": string_param(
            "Solution appliquée (depuis ITILSolution)",
            required=False,
        ),
        "followups": string_param(
            "Followups du ticket (JSON string)",
            required=False,
        ),
    },
)
async def enrichisseur_extract_knowledge(
    ticket_id: str,
    title: str,
    description: str,
    solution: Optional[str] = None,
    followups: Optional[str] = None,
) -> dict[str, Any]:
    """Extrait les connaissances structurées d'un ticket."""

    # Nettoyer les entrées
    title = title.strip() if title else ""
    description = _clean_html(description) if description else ""
    solution = _clean_html(solution) if solution else ""

    # Construire le résumé du problème
    problem_summary = f"{title}"
    if description:
        # Prendre les 500 premiers caractères de la description
        desc_preview = description[:500].strip()
        if len(description) > 500:
            desc_preview += "..."
        problem_summary = f"{title}\n\n{desc_preview}"

    # Construire le résumé de la solution
    solution_summary = ""
    if solution:
        solution_summary = solution[:1000].strip()
        if len(solution) > 1000:
            solution_summary += "..."
    elif followups:
        # Si pas de solution formelle, utiliser le dernier followup
        try:
            import json
            fups = json.loads(followups) if isinstance(followups, str) else followups
            if fups and isinstance(fups, list):
                # Prendre le dernier followup non privé
                for fu in reversed(fups):
                    if not fu.get("is_private", False):
                        solution_summary = _clean_html(fu.get("content", ""))[:1000]
                        break
        except Exception:
            pass

    if not solution_summary:
        solution_summary = "Solution non documentée - voir les followups du ticket"

    # Détecter la catégorie automatiquement
    category = _detect_category(title, description, solution_summary)

    # Générer des tags
    tags = _generate_tags(title, description, solution_summary)

    # 🆕 CALCUL DU SCORE DE QUALITÉ
    quality_score = _calculate_quality_score(
        title=title,
        description=description,
        solution_summary=solution_summary,
        category=category,
        tags=tags
    )

    # Seuil de qualité minimum : 0.4 (40%)
    quality_threshold = 0.4
    ready_for_injection = (
        bool(problem_summary and solution_summary) and
        quality_score >= quality_threshold
    )

    return {
        "success": True,
        "ticket_id": ticket_id,
        "problem_summary": problem_summary,
        "solution_summary": solution_summary,
        "category": category,
        "tags": tags,
        "quality_score": round(quality_score, 2),
        "quality_threshold": quality_threshold,
        "ready_for_injection": ready_for_injection,
        "rejection_reason": None if ready_for_injection else f"Score qualité trop faible ({quality_score:.2f} < {quality_threshold})",
    }


@tool_registry.register_function(
    name="enrichisseur_get_stats",
    description="""Récupère les statistiques d'enrichissement du RAG.
Retourne le nombre total d'entrées, les catégories, et un rapport.
SAFEGUARD: L0 (READ_ONLY)""",
    parameters={},
)
async def enrichisseur_get_stats() -> dict[str, Any]:
    """Récupère les stats d'enrichissement."""
    try:
        pool = await memory_client._get_pool()

        # Stats globales
        global_stats = await pool.fetchrow("""
            SELECT
                COUNT(*) as total_entries,
                COUNT(DISTINCT category) as total_categories,
                MIN(created_at) as oldest_entry,
                MAX(created_at) as newest_entry,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as added_last_24h,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as added_last_7d
            FROM widip_knowledge_base
        """)

        # Top catégories
        category_stats = await pool.fetch("""
            SELECT category, COUNT(*) as count
            FROM widip_knowledge_base
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)

        return {
            "success": True,
            "total_entries": global_stats["total_entries"],
            "total_categories": global_stats["total_categories"],
            "oldest_entry": str(global_stats["oldest_entry"]) if global_stats["oldest_entry"] else None,
            "newest_entry": str(global_stats["newest_entry"]) if global_stats["newest_entry"] else None,
            "added_last_24h": global_stats["added_last_24h"],
            "added_last_7d": global_stats["added_last_7d"],
            "top_categories": [
                {"category": r["category"], "count": r["count"]}
                for r in category_stats
            ],
            "report_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("enrichisseur_stats_error", error=str(e))
        return {"success": False, "error": str(e)}


@tool_registry.register_function(
    name="enrichisseur_run_batch",
    description="""Exécute un batch d'enrichissement complet.
1. Récupère les tickets résolus des dernières heures
2. Filtre ceux déjà dans le RAG
3. Extrait les connaissances
4. Injecte dans la base

Retourne un rapport détaillé de l'enrichissement.
SAFEGUARD: L1 (MINOR) - Écriture dans RAG uniquement""",
    parameters={
        "hours_since": int_param(
            "Traiter les tickets des X dernières heures",
            required=False,
            default=24,
        ),
        "max_tickets": int_param(
            "Nombre maximum de tickets à traiter",
            required=False,
            default=50,
        ),
        "dry_run": bool_param(
            "Si true, analyse sans injecter dans le RAG",
            required=False,
            default=False,
        ),
    },
)
async def enrichisseur_run_batch(
    hours_since: int = 24,
    max_tickets: int = 50,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Exécute un batch d'enrichissement."""

    logger.info(
        "enrichisseur_batch_start",
        hours_since=hours_since,
        max_tickets=max_tickets,
        dry_run=dry_run,
    )

    report = {
        "success": True,
        "dry_run": dry_run,
        "started_at": datetime.utcnow().isoformat(),
        "tickets_found": 0,
        "tickets_already_in_rag": 0,
        "tickets_processed": 0,
        "tickets_injected": 0,
        "tickets_failed": 0,
        "details": [],
    }

    try:
        # 1. Récupérer les tickets résolus
        resolved = await glpi_client.get_resolved_tickets(
            hours_since=hours_since,
            limit=max_tickets,
        )

        if not resolved.get("success"):
            report["success"] = False
            report["error"] = resolved.get("error", "Failed to get resolved tickets")
            return report

        tickets = resolved.get("tickets", [])
        report["tickets_found"] = len(tickets)

        # 2. Traiter chaque ticket
        for ticket in tickets:
            ticket_id = str(ticket.get("id", ""))
            ticket_detail = {
                "ticket_id": ticket_id,
                "title": ticket.get("title", "")[:100],
                "status": "pending",
            }

            # Vérifier si déjà dans RAG
            exists_check = await memory_check_exists(ticket_id)
            if exists_check.get("exists"):
                report["tickets_already_in_rag"] += 1
                ticket_detail["status"] = "already_exists"
                report["details"].append(ticket_detail)
                continue

            # Extraire les connaissances
            import json
            extraction = await enrichisseur_extract_knowledge(
                ticket_id=ticket_id,
                title=ticket.get("title", ""),
                description=ticket.get("description", ""),
                solution=ticket.get("solution"),
                followups=json.dumps(ticket.get("followups", [])),
            )

            if not extraction.get("ready_for_injection"):
                report["tickets_failed"] += 1
                ticket_detail["status"] = "extraction_failed"
                ticket_detail["reason"] = "Missing problem or solution"
                report["details"].append(ticket_detail)
                continue

            report["tickets_processed"] += 1

            # Injecter dans RAG (sauf dry_run)
            if not dry_run:
                inject_result = await memory_client.add_knowledge(
                    ticket_id=ticket_id,
                    problem_summary=extraction["problem_summary"],
                    solution_summary=extraction["solution_summary"],
                    category=extraction.get("category"),
                    tags=extraction.get("tags", []),
                    quality_score=extraction.get("quality_score", 0.0),
                )

                if inject_result.get("success"):
                    report["tickets_injected"] += 1
                    ticket_detail["status"] = "injected"
                    ticket_detail["knowledge_id"] = inject_result.get("id")
                else:
                    report["tickets_failed"] += 1
                    ticket_detail["status"] = "injection_failed"
                    ticket_detail["error"] = inject_result.get("error")
            else:
                ticket_detail["status"] = "dry_run_ok"
                ticket_detail["would_inject"] = {
                    "problem": extraction["problem_summary"][:100] + "...",
                    "solution": extraction["solution_summary"][:100] + "...",
                    "category": extraction.get("category"),
                    "tags": extraction.get("tags", []),
                }

            report["details"].append(ticket_detail)

        report["completed_at"] = datetime.utcnow().isoformat()

        logger.info(
            "enrichisseur_batch_complete",
            found=report["tickets_found"],
            processed=report["tickets_processed"],
            injected=report["tickets_injected"],
            failed=report["tickets_failed"],
        )

        return report

    except Exception as e:
        logger.exception("enrichisseur_batch_error", error=str(e))
        report["success"] = False
        report["error"] = str(e)
        return report


# =============================================================================
# Fonctions utilitaires
# =============================================================================

def _clean_html(text: str) -> str:
    """Nettoie le HTML du texte."""
    if not text:
        return ""

    import re

    # Supprimer les tags HTML
    text = re.sub(r'<[^>]+>', ' ', text)

    # Décoder les entités HTML courantes
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def _detect_category(title: str, description: str, solution: str) -> str:
    """Détecte automatiquement la catégorie du ticket."""
    text = f"{title} {description} {solution}".lower()

    # Mapping mot-clé → catégorie
    category_keywords = {
        "VPN": ["vpn", "tunnel", "connexion distante", "remote access"],
        "Imprimante": ["imprimante", "printer", "impression", "print", "pilote imprimante"],
        "Réseau": ["réseau", "network", "ethernet", "wifi", "internet", "connexion", "ping", "dns"],
        "Active Directory": ["ad ", "active directory", "compte", "mot de passe", "password", "ldap", "utilisateur bloqué"],
        "Messagerie": ["email", "mail", "outlook", "exchange", "boite mail", "smtp", "imap"],
        "Téléphonie": ["téléphone", "phone", "voip", "sip", "appel"],
        "Serveur": ["serveur", "server", "vm", "virtualisation", "vmware", "hyper-v"],
        "Sauvegarde": ["sauvegarde", "backup", "restore", "restauration"],
        "Sécurité": ["virus", "malware", "antivirus", "sécurité", "security", "firewall"],
        "Logiciel": ["logiciel", "application", "software", "installation", "mise à jour", "update"],
        "Matériel": ["matériel", "hardware", "pc", "ordinateur", "écran", "clavier", "souris"],
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "Autre"


def _generate_tags(title: str, description: str, solution: str) -> list[str]:
    """Génère des tags pertinents pour le ticket."""
    text = f"{title} {description} {solution}".lower()

    # Liste de tags possibles
    tag_keywords = {
        "vpn": ["vpn"],
        "windows": ["windows", "win10", "win11"],
        "réseau": ["réseau", "network", "ethernet", "wifi"],
        "mot_de_passe": ["mot de passe", "password", "mdp"],
        "imprimante": ["imprimante", "printer"],
        "outlook": ["outlook", "mail", "email"],
        "teams": ["teams", "microsoft teams"],
        "ad": ["active directory", "ad ", "ldap"],
        "urgent": ["urgent", "critique", "bloquant"],
        "client": ["client", "utilisateur"],
    }

    tags = []
    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword in text:
                tags.append(tag)
                break

    return list(set(tags))  # Dédupliquer


def _calculate_quality_score(
    title: str,
    description: str,
    solution_summary: str,
    category: str,
    tags: list[str],
) -> float:
    """
    Calcule un score de qualité pour un ticket (0.0 - 1.0).

    Critères évalués :
    - Longueur du titre (pertinence)
    - Longueur de la description
    - Longueur et qualité de la solution
    - Présence de catégorie identifiée
    - Nombre de tags pertinents
    - Détection de solutions vides ("fait", "ok", "fermé")
    """
    score = 0.0

    # 1. Titre (0-0.15 points)
    title_length = len(title.strip())
    if title_length >= 20:
        score += 0.15
    elif title_length >= 10:
        score += 0.10
    elif title_length >= 5:
        score += 0.05

    # 2. Description (0-0.20 points)
    desc_length = len(description.strip())
    if desc_length >= 100:
        score += 0.20
    elif desc_length >= 50:
        score += 0.15
    elif desc_length >= 20:
        score += 0.10
    elif desc_length >= 10:
        score += 0.05

    # 3. Solution (0-0.40 points - le plus important)
    solution_length = len(solution_summary.strip())
    solution_lower = solution_summary.lower()

    # Pénalité pour solutions vides/inutiles
    useless_solutions = [
        "fait", "ok", "fermé", "close", "résolu", "done",
        "solution non documentée", "voir les followups",
        "ras", "n/a", "na", "test"
    ]

    is_useless = any(phrase in solution_lower for phrase in useless_solutions)

    if is_useless or solution_length < 10:
        score += 0.0  # Pas de points pour solution vide
    elif solution_length >= 200:
        score += 0.40
    elif solution_length >= 100:
        score += 0.30
    elif solution_length >= 50:
        score += 0.20
    elif solution_length >= 20:
        score += 0.10

    # 4. Catégorie identifiée (0-0.10 points)
    if category and category != "Autre":
        score += 0.10
    elif category == "Autre":
        score += 0.05

    # 5. Tags (0-0.15 points)
    num_tags = len(tags)
    if num_tags >= 3:
        score += 0.15
    elif num_tags >= 2:
        score += 0.10
    elif num_tags >= 1:
        score += 0.05

    # Bonus : Solution contient des actions concrètes
    action_verbs = [
        "réinstaller", "redémarrer", "vérifier", "configurer",
        "modifier", "supprimer", "ajouter", "créer", "ouvrir",
        "fermer", "désactiver", "activer", "mettre à jour",
        "télécharger", "installer", "contacter", "appeler"
    ]

    if any(verb in solution_lower for verb in action_verbs):
        score += 0.05  # Bonus pour solution actionnable

    return min(score, 1.0)  # Cap à 1.0
