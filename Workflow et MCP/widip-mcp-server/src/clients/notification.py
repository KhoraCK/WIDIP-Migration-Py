"""
Client de notification unifié pour WIDIP.

Ce module gère les notifications vers:
- Clients finaux (via email SMTP)
- Techniciens (via email + Teams/Slack webhook)
- Système de validation humaine (SAFEGUARD L3)

Utilise le SMTPClient existant pour les emails
et des webhooks pour les notifications instantanées.
"""

from typing import Any, Optional

import httpx
import structlog

from ..config import settings
from .smtp import smtp_client

logger = structlog.get_logger(__name__)


class NotificationClient:
    """
    Client unifié pour les notifications WIDIP.

    Combine plusieurs canaux:
    - Email (SMTP) pour les notifications formelles
    - Teams/Slack webhooks pour les alertes instantanées
    """

    def __init__(self) -> None:
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP pour les webhooks."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    # =========================================================================
    # Notifications Client
    # =========================================================================

    async def notify_client(
        self,
        client_email: str,
        client_name: str,
        ticket_id: str,
        subject: str,
        message: str,
        notification_type: str = "info",
        include_ticket_link: bool = True,
    ) -> dict[str, Any]:
        """
        Envoie une notification au client final.

        Args:
            client_email: Email du client
            client_name: Nom du client (pour personnalisation)
            ticket_id: ID du ticket GLPI concerné
            subject: Sujet de la notification
            message: Corps du message
            notification_type: Type de notification (info, update, resolved)
            include_ticket_link: Inclure un lien vers le ticket

        Returns:
            Résultat de l'envoi
        """
        logger.info(
            "notify_client",
            client_email=client_email,
            ticket_id=ticket_id,
            notification_type=notification_type,
        )

        # Construire l'email HTML
        html_body = self._build_client_email_html(
            client_name=client_name,
            ticket_id=ticket_id,
            message=message,
            notification_type=notification_type,
            include_ticket_link=include_ticket_link,
        )

        # Envoyer via SMTP
        result = await smtp_client.send_email(
            to=client_email,
            subject=f"[Ticket #{ticket_id}] {subject}",
            body=message,  # Version texte
            html_body=html_body,
        )

        if result.get("success"):
            result["notification_type"] = notification_type
            result["ticket_id"] = ticket_id
            result["client_name"] = client_name

        return result

    def _build_client_email_html(
        self,
        client_name: str,
        ticket_id: str,
        message: str,
        notification_type: str,
        include_ticket_link: bool,
    ) -> str:
        """Construit le corps HTML de l'email client."""
        # Couleurs selon le type
        colors = {
            "info": "#17a2b8",
            "update": "#ffc107",
            "resolved": "#28a745",
            "error": "#dc3545",
        }
        color = colors.get(notification_type, "#6c757d")

        # Icônes selon le type
        icons = {
            "info": "ℹ️",
            "update": "🔄",
            "resolved": "✅",
            "error": "⚠️",
        }
        icon = icons.get(notification_type, "📧")

        ticket_link_html = ""
        if include_ticket_link and settings.glpi_url:
            ticket_link_html = f"""
            <p style="margin-top: 20px;">
                <a href="{settings.glpi_url}/front/ticket.form.php?id={ticket_id}"
                   style="background: {color}; color: white; padding: 10px 20px;
                          text-decoration: none; border-radius: 5px;">
                    Voir le ticket #{ticket_id}
                </a>
            </p>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: {color}; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{icon} Ticket #{ticket_id}</h1>
    </div>
    <div class="content">
        <p>Bonjour {client_name},</p>
        <p>{message}</p>
        {ticket_link_html}
    </div>
    <div class="footer">
        <p>Cet email a été envoyé automatiquement par le système WIDIP.</p>
        <p>© {settings.smtp_from_name}</p>
    </div>
</body>
</html>
"""

    # =========================================================================
    # Notifications Technicien
    # =========================================================================

    async def notify_technician(
        self,
        ticket_id: str,
        subject: str,
        message: str,
        priority: str = "normal",
        assigned_technician: Optional[str] = None,
        channels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Notifie un ou plusieurs techniciens.

        Args:
            ticket_id: ID du ticket concerné
            subject: Sujet de la notification
            message: Corps du message
            priority: Priorité (low, normal, high, critical)
            assigned_technician: Email du technicien assigné (optionnel)
            channels: Canaux à utiliser ["email", "teams", "slack"]

        Returns:
            Résultat des notifications par canal
        """
        logger.info(
            "notify_technician",
            ticket_id=ticket_id,
            priority=priority,
            assigned_technician=assigned_technician,
        )

        # Canaux par défaut selon la priorité
        if channels is None:
            if priority in ("high", "critical"):
                channels = ["email", "teams"]
            else:
                channels = ["email"]

        results: dict[str, Any] = {
            "success": True,
            "ticket_id": ticket_id,
            "priority": priority,
            "channels_attempted": channels,
            "channels_results": {},
        }

        # Envoi par email
        if "email" in channels:
            tech_email = assigned_technician or settings.smtp_from_email
            email_result = await smtp_client.send_email(
                to=tech_email,
                subject=f"[{priority.upper()}] Ticket #{ticket_id}: {subject}",
                body=message,
                html_body=self._build_technician_email_html(
                    ticket_id=ticket_id,
                    subject=subject,
                    message=message,
                    priority=priority,
                ),
            )
            results["channels_results"]["email"] = email_result

        # Envoi via Teams webhook
        if "teams" in channels:
            teams_result = await self._send_teams_notification(
                ticket_id=ticket_id,
                subject=subject,
                message=message,
                priority=priority,
            )
            results["channels_results"]["teams"] = teams_result

        # Envoi via Slack webhook
        if "slack" in channels:
            slack_result = await self._send_slack_notification(
                ticket_id=ticket_id,
                subject=subject,
                message=message,
                priority=priority,
            )
            results["channels_results"]["slack"] = slack_result

        # Vérifier si au moins un canal a réussi
        any_success = any(
            r.get("success", False)
            for r in results["channels_results"].values()
        )
        results["success"] = any_success

        return results

    def _build_technician_email_html(
        self,
        ticket_id: str,
        subject: str,
        message: str,
        priority: str,
    ) -> str:
        """Construit le corps HTML de l'email technicien."""
        priority_colors = {
            "low": "#6c757d",
            "normal": "#17a2b8",
            "high": "#ffc107",
            "critical": "#dc3545",
        }
        color = priority_colors.get(priority, "#6c757d")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .priority-badge {{
            background: {color};
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
        }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="content">
        <h2>Ticket #{ticket_id}: {subject}</h2>
        <p><span class="priority-badge">{priority.upper()}</span></p>
        <p>{message}</p>
        <hr>
        <p><small>Notification WIDIP - Action requise</small></p>
    </div>
</body>
</html>
"""

    async def _send_teams_notification(
        self,
        ticket_id: str,
        subject: str,
        message: str,
        priority: str,
    ) -> dict[str, Any]:
        """Envoie une notification via Microsoft Teams webhook."""
        teams_webhook_url = getattr(settings, "teams_webhook_url", "")

        if not teams_webhook_url:
            return {
                "success": False,
                "error": "Teams webhook URL not configured",
            }

        # Couleurs Teams selon priorité
        theme_colors = {
            "low": "808080",
            "normal": "0078D7",
            "high": "FFC107",
            "critical": "DC3545",
        }

        # Format Adaptive Card pour Teams
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_colors.get(priority, "0078D7"),
            "summary": f"Ticket #{ticket_id}: {subject}",
            "sections": [
                {
                    "activityTitle": f"🎫 Ticket #{ticket_id}",
                    "activitySubtitle": subject,
                    "facts": [
                        {"name": "Priorité", "value": priority.upper()},
                    ],
                    "text": message,
                    "markdown": True,
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Voir le ticket",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"{settings.glpi_url}/front/ticket.form.php?id={ticket_id}",
                        }
                    ],
                }
            ] if settings.glpi_url else [],
        }

        try:
            response = await self.http_client.post(teams_webhook_url, json=payload)
            if response.is_success:
                logger.info("teams_notification_sent", ticket_id=ticket_id)
                return {"success": True, "channel": "teams"}
            else:
                logger.warning(
                    "teams_notification_failed",
                    ticket_id=ticket_id,
                    status=response.status_code,
                )
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.exception("teams_notification_error", error=str(e))
            return {"success": False, "error": str(e)}

    async def _send_slack_notification(
        self,
        ticket_id: str,
        subject: str,
        message: str,
        priority: str,
    ) -> dict[str, Any]:
        """Envoie une notification via Slack webhook."""
        slack_webhook_url = getattr(settings, "slack_webhook_url", "")

        if not slack_webhook_url:
            return {
                "success": False,
                "error": "Slack webhook URL not configured",
            }

        # Emojis selon priorité
        priority_emojis = {
            "low": "ℹ️",
            "normal": "📋",
            "high": "⚠️",
            "critical": "🚨",
        }
        emoji = priority_emojis.get(priority, "📋")

        # Format Slack Block Kit
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Ticket #{ticket_id}: {subject}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Priorité:* {priority.upper()}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message,
                    },
                },
            ],
        }

        try:
            response = await self.http_client.post(slack_webhook_url, json=payload)
            if response.is_success:
                logger.info("slack_notification_sent", ticket_id=ticket_id)
                return {"success": True, "channel": "slack"}
            else:
                logger.warning(
                    "slack_notification_failed",
                    ticket_id=ticket_id,
                    status=response.status_code,
                )
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.exception("slack_notification_error", error=str(e))
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Validation Humaine (SAFEGUARD L3)
    # =========================================================================

    async def request_human_validation(
        self,
        action_type: str,
        action_description: str,
        ticket_id: Optional[str] = None,
        affected_entity: Optional[str] = None,
        urgency: str = "normal",
        expiration_minutes: int = 60,
        notification_channels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Demande une validation humaine pour une action sensible (SAFEGUARD L3).

        Cette fonction est appelée avant d'exécuter des actions comme:
        - ad_reset_password
        - ad_disable_account
        - glpi_close_ticket

        Args:
            action_type: Type d'action (ex: "ad_reset_password")
            action_description: Description lisible de l'action
            ticket_id: ID du ticket associé (optionnel)
            affected_entity: Entité affectée (ex: nom d'utilisateur, ID ticket)
            urgency: Niveau d'urgence (low, normal, high)
            expiration_minutes: Délai d'expiration de la demande
            notification_channels: Canaux de notification ["email", "teams", "slack"]

        Returns:
            Informations sur la demande de validation créée
        """
        import uuid
        from datetime import datetime, timedelta

        logger.info(
            "request_human_validation",
            action_type=action_type,
            affected_entity=affected_entity,
            urgency=urgency,
        )

        # Générer un ID de validation unique
        validation_id = f"VALID-{action_type.upper()}-{uuid.uuid4().hex[:8].upper()}"

        # Calculer l'expiration
        expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)

        # Canaux par défaut
        if notification_channels is None:
            if urgency == "high":
                notification_channels = ["email", "teams"]
            else:
                notification_channels = ["email"]

        # Construire le message de demande
        message = self._build_validation_message(
            validation_id=validation_id,
            action_type=action_type,
            action_description=action_description,
            ticket_id=ticket_id,
            affected_entity=affected_entity,
            urgency=urgency,
            expires_at=expires_at,
        )

        # Notifier les techniciens
        notification_result = await self.notify_technician(
            ticket_id=ticket_id or "N/A",
            subject=f"Validation requise: {action_type}",
            message=message,
            priority=urgency,
            channels=notification_channels,
        )

        return {
            "success": True,
            "validation_id": validation_id,
            "action_type": action_type,
            "action_description": action_description,
            "affected_entity": affected_entity,
            "ticket_id": ticket_id,
            "status": "pending",
            "urgency": urgency,
            "expires_at": expires_at.isoformat(),
            "expiration_minutes": expiration_minutes,
            "notification_sent": notification_result.get("success", False),
            "notification_channels": notification_channels,
            "message": (
                "Demande de validation créée. "
                f"En attente d'approbation humaine. "
                f"Expire dans {expiration_minutes} minutes."
            ),
        }

    def _build_validation_message(
        self,
        validation_id: str,
        action_type: str,
        action_description: str,
        ticket_id: Optional[str],
        affected_entity: Optional[str],
        urgency: str,
        expires_at: Any,
    ) -> str:
        """Construit le message de demande de validation."""
        lines = [
            f"🔒 VALIDATION HUMAINE REQUISE",
            f"",
            f"**ID Demande:** {validation_id}",
            f"**Action:** {action_type}",
            f"**Description:** {action_description}",
        ]

        if affected_entity:
            lines.append(f"**Entité affectée:** {affected_entity}")

        if ticket_id:
            lines.append(f"**Ticket associé:** #{ticket_id}")

        lines.extend([
            f"**Urgence:** {urgency.upper()}",
            f"**Expire:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"",
            f"Veuillez approuver ou refuser cette action via le Dashboard SAFEGUARD.",
        ])

        return "\n".join(lines)


# Instance singleton
notification_client = NotificationClient()
