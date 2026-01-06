"""
Health Check Workflow

Monitors GLPI availability and manages circuit breaker.
Runs every 30 seconds.

Equivalent to: WIDIP_Health_Check_GLPI_v2.json
"""

from datetime import datetime
from typing import Any

import httpx
import structlog

from workflows.core.base import WorkflowBase, WorkflowStatus
from workflows.core.context import WorkflowContext
from workflows.core.config import settings

logger = structlog.get_logger()


class HealthCheckWorkflow(WorkflowBase):
    """
    Health Check Workflow - GLPI Monitoring + Circuit Breaker

    Flow:
    1. Ping GLPI API (/apirest.php/initSession)
    2. Update Redis health status (ok/down/degraded)
    3. If DOWN: Send alert (with anti-spam)
    4. If recovered: Send recovery alert
    """

    name = "health_check"
    description = "GLPI health monitoring and circuit breaker"
    timeout_seconds = 15
    safeguard_level = "L0"

    # Health check configuration
    PING_TIMEOUT_MS = 5000
    HEALTH_STATUS_TTL = 60  # seconds
    ALERT_COOLDOWN_TTL = 300  # 5 minutes anti-spam

    async def execute(self, ctx: WorkflowContext) -> dict:
        """
        Execute health check workflow.

        Returns:
            dict with status, was_down, alert_sent
        """
        # 1. Ping GLPI
        status, error_message = await self._ping_glpi()

        logger.debug(
            "health_check_ping",
            service="glpi",
            status=status,
            error=error_message,
        )

        # 2. Get previous status
        previous_status = await self.redis.get_health_status("glpi")

        # 3. Update Redis health status
        await self.redis.set_health_status(
            "glpi",
            status,
            ttl_seconds=self.HEALTH_STATUS_TTL,
        )

        # 4. Handle state transitions
        alert_sent = False
        recovery_sent = False

        if status == "down":
            # Check if we should send alert (anti-spam)
            if not await self.redis.is_alert_sent("glpi_down"):
                await self._send_down_alert(error_message)
                await self.redis.mark_alert_sent("glpi_down", self.ALERT_COOLDOWN_TTL)
                alert_sent = True
                logger.warning(
                    "glpi_down_alert_sent",
                    error=error_message,
                )
            else:
                logger.debug("glpi_down_alert_suppressed", reason="cooldown")

        elif status == "ok" and previous_status == "down":
            # Recovery detected
            await self._send_recovery_alert()
            await self.redis.clear_alert_sent("glpi_down")
            recovery_sent = True
            logger.info("glpi_recovered")

        # Store state for debugging
        ctx.set_state("status", status)
        ctx.set_state("previous_status", previous_status)
        ctx.set_state("alert_sent", alert_sent)
        ctx.set_state("recovery_sent", recovery_sent)

        return {
            "status": status,
            "previous_status": previous_status,
            "error_message": error_message,
            "alert_sent": alert_sent,
            "recovery_sent": recovery_sent,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _ping_glpi(self) -> tuple[str, str]:
        """
        Ping GLPI API to check availability.

        Returns:
            Tuple of (status, error_message)
            status: 'ok', 'down', or 'degraded'
        """
        if not settings.glpi_url:
            logger.warning("glpi_url_not_configured")
            return "unknown", "GLPI URL not configured"

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.PING_TIMEOUT_MS / 1000)
            ) as client:
                # Build headers
                headers = {}
                if settings.glpi_app_token:
                    headers["App-Token"] = settings.glpi_app_token.get_secret_value()
                if settings.glpi_user_token:
                    headers["Authorization"] = f"user_token {settings.glpi_user_token.get_secret_value()}"

                # Ping initSession endpoint
                response = await client.get(
                    f"{settings.glpi_url}/apirest.php/initSession",
                    headers=headers,
                )

                # Analyze response
                if response.status_code == 200:
                    data = response.json()
                    if "session_token" in data:
                        return "ok", None
                    return "degraded", "No session token in response"

                if response.status_code in (401, 403):
                    return "degraded", f"Authentication error: {response.status_code}"

                if response.status_code >= 500:
                    return "down", f"Server error: {response.status_code}"

                return "degraded", f"Unexpected status: {response.status_code}"

        except httpx.TimeoutException:
            return "down", "Connection timeout"

        except httpx.ConnectError as e:
            return "down", f"Connection error: {str(e)}"

        except Exception as e:
            return "down", f"Unexpected error: {str(e)}"

    async def _send_down_alert(self, error_message: str) -> None:
        """Send GLPI down alert via Slack/notification"""
        if not settings.slack_webhook_url:
            logger.debug("slack_webhook_not_configured", skipping="down_alert")
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": "🚨 *GLPI DOWN* - Circuit Breaker Active",
                        "attachments": [
                            {
                                "color": "danger",
                                "fields": [
                                    {
                                        "title": "Service",
                                        "value": "GLPI",
                                        "short": True,
                                    },
                                    {
                                        "title": "Status",
                                        "value": "DOWN",
                                        "short": True,
                                    },
                                    {
                                        "title": "Error",
                                        "value": error_message or "Unknown",
                                        "short": False,
                                    },
                                    {
                                        "title": "Impact",
                                        "value": "SENTINEL en mode dégradé, SUPPORT suspendu",
                                        "short": False,
                                    },
                                ],
                                "footer": "WIDIP Health Check",
                                "ts": int(datetime.utcnow().timestamp()),
                            }
                        ],
                    },
                    timeout=10.0,
                )
        except Exception as e:
            logger.error("slack_alert_failed", error=str(e))

    async def _send_recovery_alert(self) -> None:
        """Send GLPI recovery alert via Slack/notification"""
        if not settings.slack_webhook_url:
            logger.debug("slack_webhook_not_configured", skipping="recovery_alert")
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": "✅ *GLPI RECOVERED* - Services Resumed",
                        "attachments": [
                            {
                                "color": "good",
                                "fields": [
                                    {
                                        "title": "Service",
                                        "value": "GLPI",
                                        "short": True,
                                    },
                                    {
                                        "title": "Status",
                                        "value": "OK",
                                        "short": True,
                                    },
                                    {
                                        "title": "Info",
                                        "value": "Tous les workflows reprennent leur fonctionnement normal",
                                        "short": False,
                                    },
                                ],
                                "footer": "WIDIP Health Check",
                                "ts": int(datetime.utcnow().timestamp()),
                            }
                        ],
                    },
                    timeout=10.0,
                )
        except Exception as e:
            logger.error("slack_recovery_alert_failed", error=str(e))

    async def on_error(self, ctx: WorkflowContext, error: Exception) -> None:
        """Handle errors - set status to unknown"""
        await self.redis.set_health_status(
            "glpi",
            "unknown",
            ttl_seconds=self.HEALTH_STATUS_TTL,
        )
        logger.error(
            "health_check_error",
            error=str(error),
            workflow_id=ctx.workflow_id,
        )
