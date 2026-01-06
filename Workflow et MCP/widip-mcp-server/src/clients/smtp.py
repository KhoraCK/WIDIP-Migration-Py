"""
Client SMTP pour l'envoi d'emails.

Utilisé pour les notifications et communications automatisées.
"""

from typing import Any, Optional

import aiosmtplib
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

logger = structlog.get_logger(__name__)


class SMTPClient:
    """
    Client SMTP asynchrone pour l'envoi d'emails.
    """

    def __init__(self) -> None:
        self._smtp: Optional[aiosmtplib.SMTP] = None

    async def _get_connection(self) -> aiosmtplib.SMTP:
        """Retourne une connexion SMTP."""
        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=settings.smtp_use_tls,
        )
        await smtp.connect()

        if settings.smtp_user:
            await smtp.login(
                settings.smtp_user,
                settings.smtp_pass.get_secret_value(),
            )

        return smtp

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Envoie un email.

        Args:
            to: Destinataire principal
            subject: Sujet de l'email
            body: Corps du message (texte)
            html_body: Corps du message (HTML, optionnel)
            cc: Destinataires en copie
            bcc: Destinataires en copie cachée

        Returns:
            Résultat de l'envoi
        """
        logger.info("smtp_send", to=to, subject=subject[:50])

        try:
            # Créer le message
            if html_body:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(body, "plain", "utf-8"))
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            else:
                msg = MIMEText(body, "plain", "utf-8")

            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg["To"] = to

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Liste complète des destinataires
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Envoyer
            smtp = await self._get_connection()
            try:
                await smtp.send_message(msg, recipients=recipients)
                logger.info("smtp_sent", to=to)
                return {
                    "success": True,
                    "to": to,
                    "subject": subject,
                    "message": "Email envoyé avec succès",
                }
            finally:
                await smtp.quit()

        except Exception as e:
            logger.exception("smtp_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
            }


# Instance singleton
smtp_client = SMTPClient()
