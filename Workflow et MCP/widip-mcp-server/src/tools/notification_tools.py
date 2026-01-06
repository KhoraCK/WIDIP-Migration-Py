"""
Tools MCP pour les notifications.

Ce module expose les outils de notification aux agents IA:
- Notification client (email)
- Notification technicien (email + Teams/Slack)
- Demande de validation humaine (SAFEGUARD L3)

Référence: WIDIP_ARCHITECTURE_v15.md - Section 4 "Module Notification"
"""

from typing import Any, Optional

from ..clients.notification import notification_client
from ..mcp.registry import (
    tool_registry,
    string_param,
    int_param,
    bool_param,
    array_param,
)


@tool_registry.register_function(
    name="notify_client",
    description="""Envoie une notification au client final par email.
Utilise ce tool pour informer le client de l'avancement de son ticket:
- Prise en charge du ticket
- Mise à jour du diagnostic
- Résolution du problème
- Demande d'information complémentaire

Le client reçoit un email formaté avec un lien vers son ticket GLPI.""",
    parameters={
        "client_email": string_param(
            "Adresse email du client",
            required=True,
        ),
        "client_name": string_param(
            "Nom du client (pour personnalisation de l'email)",
            required=True,
        ),
        "ticket_id": string_param(
            "ID du ticket GLPI concerné",
            required=True,
        ),
        "subject": string_param(
            "Sujet de la notification",
            required=True,
        ),
        "message": string_param(
            "Corps du message à envoyer au client",
            required=True,
        ),
        "notification_type": string_param(
            "Type de notification: info, update, resolved, error",
            required=False,
            default="info",
            enum=["info", "update", "resolved", "error"],
        ),
        "include_ticket_link": bool_param(
            "Inclure un lien vers le ticket GLPI dans l'email",
            required=False,
            default=True,
        ),
    },
)
async def notify_client(
    client_email: str,
    client_name: str,
    ticket_id: str,
    subject: str,
    message: str,
    notification_type: str = "info",
    include_ticket_link: bool = True,
) -> dict[str, Any]:
    """Envoie une notification au client final."""
    result = await notification_client.notify_client(
        client_email=client_email,
        client_name=client_name,
        ticket_id=ticket_id,
        subject=subject,
        message=message,
        notification_type=notification_type,
        include_ticket_link=include_ticket_link,
    )
    result["operation"] = "notify_client"
    return result


@tool_registry.register_function(
    name="notify_technician",
    description="""Envoie une notification à un ou plusieurs techniciens.
Utilise ce tool pour alerter les techniciens sur:
- Nouvelle alerte réseau nécessitant attention
- Ticket escaladé nécessitant intervention
- Demande de vérification (ex: Phibee)
- Incident critique

Les notifications peuvent être envoyées par email et/ou Teams/Slack
selon la priorité et la configuration.""",
    parameters={
        "ticket_id": string_param(
            "ID du ticket concerné",
            required=True,
        ),
        "subject": string_param(
            "Sujet de la notification",
            required=True,
        ),
        "message": string_param(
            "Corps du message pour le technicien",
            required=True,
        ),
        "priority": string_param(
            "Priorité de la notification: low, normal, high, critical",
            required=False,
            default="normal",
            enum=["low", "normal", "high", "critical"],
        ),
        "assigned_technician": string_param(
            "Email du technicien assigné (optionnel, sinon broadcast)",
            required=False,
        ),
        "channels": array_param(
            "Canaux de notification: email, teams, slack",
            required=False,
        ),
    },
)
async def notify_technician(
    ticket_id: str,
    subject: str,
    message: str,
    priority: str = "normal",
    assigned_technician: Optional[str] = None,
    channels: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Envoie une notification aux techniciens."""
    result = await notification_client.notify_technician(
        ticket_id=ticket_id,
        subject=subject,
        message=message,
        priority=priority,
        assigned_technician=assigned_technician,
        channels=channels,
    )
    result["operation"] = "notify_technician"
    return result


@tool_registry.register_function(
    name="request_human_validation",
    description="""Demande une validation humaine pour une action sensible (SAFEGUARD L3).

Ce tool est utilisé AVANT d'exécuter des actions sensibles qui requièrent
une approbation humaine selon les règles SAFEGUARD:
- Reset de mot de passe (ad_reset_password)
- Désactivation de compte (ad_disable_account)
- Clôture de ticket (glpi_close_ticket)

La demande est envoyée aux techniciens qui peuvent approuver ou refuser
via le Dashboard SAFEGUARD ou les liens dans la notification.

Retourne un ID de validation à utiliser pour vérifier le statut.""",
    parameters={
        "action_type": string_param(
            "Type d'action sensible (ex: ad_reset_password, glpi_close_ticket)",
            required=True,
        ),
        "action_description": string_param(
            "Description lisible de l'action à valider",
            required=True,
        ),
        "ticket_id": string_param(
            "ID du ticket associé (si applicable)",
            required=False,
        ),
        "affected_entity": string_param(
            "Entité affectée par l'action (ex: nom utilisateur, ID ressource)",
            required=False,
        ),
        "urgency": string_param(
            "Niveau d'urgence: low, normal, high",
            required=False,
            default="normal",
            enum=["low", "normal", "high"],
        ),
        "expiration_minutes": int_param(
            "Délai d'expiration de la demande en minutes (défaut: 60)",
            required=False,
            default=60,
        ),
        "notification_channels": array_param(
            "Canaux de notification pour les approbateurs: email, teams, slack",
            required=False,
        ),
    },
)
async def request_human_validation(
    action_type: str,
    action_description: str,
    ticket_id: Optional[str] = None,
    affected_entity: Optional[str] = None,
    urgency: str = "normal",
    expiration_minutes: int = 60,
    notification_channels: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Demande une validation humaine pour une action sensible."""
    result = await notification_client.request_human_validation(
        action_type=action_type,
        action_description=action_description,
        ticket_id=ticket_id,
        affected_entity=affected_entity,
        urgency=urgency,
        expiration_minutes=expiration_minutes,
        notification_channels=notification_channels,
    )
    result["operation"] = "request_human_validation"
    return result
