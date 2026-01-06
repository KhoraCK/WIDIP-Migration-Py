"""
SAFEGUARD Workflow

Human-in-the-loop approval system for critical MCP operations.
Manages approval requests, notifications, and execution after approval.

Equivalent to: WIDIP_Safeguard_v2.json
"""

from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import structlog

from workflows.core.base import WorkflowBase
from workflows.core.context import WorkflowContext
from workflows.core.config import settings

from .models import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    CreateApprovalRequest,
    ResolveApprovalRequest,
    SafeguardLevel,
)

logger = structlog.get_logger()


class SafeguardService:
    """
    Service for managing SAFEGUARD approval requests.

    Handles CRUD operations for approvals stored in Redis.
    For production: migrate to PostgreSQL for persistence.
    """

    # Redis key prefixes
    KEY_PREFIX = "safeguard:"
    KEY_PENDING = "safeguard:pending"
    KEY_REQUEST = "safeguard:request:"

    # Default expiration
    DEFAULT_EXPIRY_MINUTES = 60

    def __init__(self, redis_client, mcp_client=None):
        self.redis = redis_client
        self.mcp = mcp_client

    async def create_request(
        self,
        request: CreateApprovalRequest,
        caller_ip: str = None,
        caller_user: str = None,
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            request: Approval request data
            caller_ip: IP of the caller
            caller_user: Username of the caller

        Returns:
            Created ApprovalRequest
        """
        # Create approval request
        approval = ApprovalRequest(
            tool_name=request.tool_name,
            arguments=request.arguments,
            safeguard_level=request.safeguard_level,
            workflow_name=request.workflow_name,
            workflow_id=request.workflow_id,
            confidence=request.confidence,
            reasoning=request.reasoning,
            risk_assessment=request.risk_assessment,
            caller_ip=caller_ip,
            caller_user=caller_user,
            expires_at=datetime.utcnow() + timedelta(minutes=request.expires_in_minutes),
        )

        # Store in Redis
        await self._store_request(approval)

        logger.info(
            "safeguard_request_created",
            request_id=approval.id,
            tool_name=approval.tool_name,
            safeguard_level=approval.safeguard_level.value,
            expires_at=approval.expires_at.isoformat(),
        )

        return approval

    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID"""
        key = f"{self.KEY_REQUEST}{request_id}"
        data = await self.redis.get(key)

        if not data:
            return None

        try:
            return ApprovalRequest.model_validate_json(data)
        except Exception as e:
            logger.error("safeguard_parse_error", request_id=request_id, error=str(e))
            return None

    async def list_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests"""
        pending_ids = await self.redis.smembers(self.KEY_PENDING)

        requests = []
        for request_id in pending_ids:
            request = await self.get_request(request_id)
            if request:
                # Check if expired
                if request.is_expired():
                    await self._mark_expired(request)
                elif request.status == ApprovalStatus.PENDING:
                    requests.append(request)

        # Sort by created_at (oldest first)
        requests.sort(key=lambda r: r.created_at)

        return requests

    async def approve(
        self,
        request_id: str,
        resolved_by: str,
        resolution_note: str = None,
    ) -> ApprovalResponse:
        """
        Approve a request and execute the MCP tool.

        Args:
            request_id: ID of the request
            resolved_by: Username of approver
            resolution_note: Optional note

        Returns:
            ApprovalResponse with execution result
        """
        request = await self.get_request(request_id)

        if not request:
            raise ValueError(f"Request not found: {request_id}")

        if not request.can_be_approved():
            raise ValueError(f"Request cannot be approved: {request.status.value}")

        # Update status
        request.status = ApprovalStatus.APPROVED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = resolved_by
        request.resolution_note = resolution_note

        # Execute the MCP tool
        execution_result = None
        execution_error = None

        if self.mcp:
            try:
                execution_result = await self.mcp.call(
                    request.tool_name,
                    request.arguments,
                )
                request.execution_result = execution_result

                logger.info(
                    "safeguard_tool_executed",
                    request_id=request_id,
                    tool_name=request.tool_name,
                    success=True,
                )

            except Exception as e:
                execution_error = str(e)
                request.execution_error = execution_error

                logger.error(
                    "safeguard_tool_execution_failed",
                    request_id=request_id,
                    tool_name=request.tool_name,
                    error=execution_error,
                )
        else:
            logger.warning("safeguard_mcp_not_configured", request_id=request_id)

        # Save updated request
        await self._store_request(request)
        await self._remove_from_pending(request_id)

        logger.info(
            "safeguard_request_approved",
            request_id=request_id,
            resolved_by=resolved_by,
            tool_name=request.tool_name,
        )

        return ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.APPROVED,
            resolved_by=resolved_by,
            resolution_note=resolution_note,
            execution_result=execution_result,
            execution_error=execution_error,
        )

    async def reject(
        self,
        request_id: str,
        resolved_by: str,
        resolution_note: str = None,
    ) -> ApprovalResponse:
        """
        Reject an approval request.

        Args:
            request_id: ID of the request
            resolved_by: Username of rejector
            resolution_note: Reason for rejection

        Returns:
            ApprovalResponse
        """
        request = await self.get_request(request_id)

        if not request:
            raise ValueError(f"Request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request already resolved: {request.status.value}")

        # Update status
        request.status = ApprovalStatus.REJECTED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = resolved_by
        request.resolution_note = resolution_note

        # Save updated request
        await self._store_request(request)
        await self._remove_from_pending(request_id)

        logger.info(
            "safeguard_request_rejected",
            request_id=request_id,
            resolved_by=resolved_by,
            tool_name=request.tool_name,
            reason=resolution_note,
        )

        return ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.REJECTED,
            resolved_by=resolved_by,
            resolution_note=resolution_note,
        )

    async def cleanup_expired(self) -> int:
        """
        Cleanup expired approval requests.

        Returns:
            Number of expired requests cleaned up
        """
        pending_ids = await self.redis.smembers(self.KEY_PENDING)
        expired_count = 0

        for request_id in pending_ids:
            request = await self.get_request(request_id)
            if request and request.is_expired():
                await self._mark_expired(request)
                expired_count += 1

        if expired_count > 0:
            logger.info(
                "safeguard_cleanup_completed",
                expired_count=expired_count,
            )

        return expired_count

    async def _store_request(self, request: ApprovalRequest) -> None:
        """Store request in Redis"""
        key = f"{self.KEY_REQUEST}{request.id}"

        # Calculate TTL (24 hours after expiration for audit)
        if request.expires_at:
            ttl = int((request.expires_at - datetime.utcnow()).total_seconds()) + 86400
        else:
            ttl = 86400 * 7  # 7 days default

        await self.redis.setex(key, ttl, request.model_dump_json())

        # Add to pending set if still pending
        if request.status == ApprovalStatus.PENDING:
            await self.redis.sadd(self.KEY_PENDING, request.id)

    async def _remove_from_pending(self, request_id: str) -> None:
        """Remove request from pending set"""
        await self.redis.srem(self.KEY_PENDING, request_id)

    async def _mark_expired(self, request: ApprovalRequest) -> None:
        """Mark request as expired"""
        request.status = ApprovalStatus.EXPIRED
        request.resolved_at = datetime.utcnow()
        await self._store_request(request)
        await self._remove_from_pending(request.id)

        logger.info(
            "safeguard_request_expired",
            request_id=request.id,
            tool_name=request.tool_name,
        )


class SafeguardNotifier:
    """
    Notification service for SAFEGUARD approvals.

    Sends notifications via Slack and/or Email.
    """

    def __init__(self, base_url: str = "http://localhost:3002"):
        """
        Initialize notifier.

        Args:
            base_url: Base URL for approval links
        """
        self.base_url = base_url.rstrip("/")

    async def notify_approval_needed(
        self,
        request: ApprovalRequest,
        channels: list[str] = None,
    ) -> dict:
        """
        Send notification for new approval request.

        Args:
            request: The approval request
            channels: Notification channels (slack, email)

        Returns:
            dict with notification results
        """
        channels = channels or ["slack"]
        results = {}

        approve_url = f"{self.base_url}/safeguard/approve/{request.id}"
        reject_url = f"{self.base_url}/safeguard/reject/{request.id}"
        dashboard_url = f"{self.base_url}/safeguard/pending"

        if "slack" in channels:
            results["slack"] = await self._send_slack_notification(
                request, approve_url, reject_url, dashboard_url
            )

        if "email" in channels:
            results["email"] = await self._send_email_notification(
                request, approve_url, reject_url, dashboard_url
            )

        return results

    async def notify_approved(self, request: ApprovalRequest) -> dict:
        """Notify that a request was approved"""
        if not settings.slack_webhook_url:
            return {"slack": "not_configured"}

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": f"✅ *SAFEGUARD APPROVED* - {request.tool_name}",
                        "attachments": [
                            {
                                "color": "good",
                                "fields": [
                                    {"title": "Tool", "value": request.tool_name, "short": True},
                                    {"title": "Approved By", "value": request.resolved_by or "N/A", "short": True},
                                    {"title": "Request ID", "value": request.id[:8], "short": True},
                                ],
                                "footer": "WIDIP SAFEGUARD",
                                "ts": int(datetime.utcnow().timestamp()),
                            }
                        ],
                    },
                    timeout=10.0,
                )
            return {"slack": "sent"}
        except Exception as e:
            logger.error("safeguard_slack_notify_approved_failed", error=str(e))
            return {"slack": f"error: {e}"}

    async def notify_rejected(self, request: ApprovalRequest) -> dict:
        """Notify that a request was rejected"""
        if not settings.slack_webhook_url:
            return {"slack": "not_configured"}

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": f"❌ *SAFEGUARD REJECTED* - {request.tool_name}",
                        "attachments": [
                            {
                                "color": "danger",
                                "fields": [
                                    {"title": "Tool", "value": request.tool_name, "short": True},
                                    {"title": "Rejected By", "value": request.resolved_by or "N/A", "short": True},
                                    {"title": "Reason", "value": request.resolution_note or "No reason provided", "short": False},
                                ],
                                "footer": "WIDIP SAFEGUARD",
                                "ts": int(datetime.utcnow().timestamp()),
                            }
                        ],
                    },
                    timeout=10.0,
                )
            return {"slack": "sent"}
        except Exception as e:
            logger.error("safeguard_slack_notify_rejected_failed", error=str(e))
            return {"slack": f"error: {e}"}

    async def _send_slack_notification(
        self,
        request: ApprovalRequest,
        approve_url: str,
        reject_url: str,
        dashboard_url: str,
    ) -> str:
        """Send Slack notification"""
        if not settings.slack_webhook_url:
            logger.debug("slack_webhook_not_configured")
            return "not_configured"

        # Build risk indicator
        risk_emoji = "🔴" if request.safeguard_level == SafeguardLevel.L4 else "🟡"
        confidence_pct = int(request.confidence * 100)

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": f"{risk_emoji} *SAFEGUARD APPROVAL REQUIRED* - Level {request.safeguard_level.value}",
                        "attachments": [
                            {
                                "color": "warning",
                                "fields": [
                                    {
                                        "title": "Tool",
                                        "value": f"`{request.tool_name}`",
                                        "short": True,
                                    },
                                    {
                                        "title": "Level",
                                        "value": request.safeguard_level.value,
                                        "short": True,
                                    },
                                    {
                                        "title": "Confidence",
                                        "value": f"{confidence_pct}%",
                                        "short": True,
                                    },
                                    {
                                        "title": "Request ID",
                                        "value": request.id[:8],
                                        "short": True,
                                    },
                                    {
                                        "title": "Arguments",
                                        "value": f"```{str(request.arguments)[:200]}```",
                                        "short": False,
                                    },
                                    {
                                        "title": "AI Reasoning",
                                        "value": request.reasoning or "N/A",
                                        "short": False,
                                    },
                                ],
                                "footer": f"Expires: {request.expires_at.strftime('%Y-%m-%d %H:%M UTC') if request.expires_at else 'Never'}",
                                "ts": int(datetime.utcnow().timestamp()),
                            },
                            {
                                "color": "#36a64f",
                                "text": f"<{approve_url}|✅ Approve> | <{reject_url}|❌ Reject> | <{dashboard_url}|📋 Dashboard>",
                            },
                        ],
                    },
                    timeout=10.0,
                )

            logger.debug("safeguard_slack_notification_sent", request_id=request.id)
            return "sent"

        except Exception as e:
            logger.error("safeguard_slack_notification_failed", error=str(e))
            return f"error: {e}"

    async def _send_email_notification(
        self,
        request: ApprovalRequest,
        approve_url: str,
        reject_url: str,
        dashboard_url: str,
    ) -> str:
        """Send email notification (placeholder)"""
        # TODO: Implement email notifications with aiosmtplib
        logger.debug("safeguard_email_notification_skipped", reason="not_implemented")
        return "not_implemented"


class SafeguardCleanupWorkflow(WorkflowBase):
    """
    SAFEGUARD Cleanup Workflow

    Runs hourly to clean up expired approval requests.
    """

    name = "safeguard_cleanup"
    description = "Clean up expired SAFEGUARD approval requests"
    timeout_seconds = 30
    safeguard_level = "L0"

    async def execute(self, ctx: WorkflowContext) -> dict:
        """Execute cleanup"""
        service = SafeguardService(self.redis, self.mcp)
        expired_count = await service.cleanup_expired()

        ctx.set_state("expired_count", expired_count)

        return {
            "expired_count": expired_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
