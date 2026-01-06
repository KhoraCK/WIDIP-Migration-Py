"""
SAFEGUARD Data Models

Approval request and response models for human-in-the-loop validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SafeguardLevel(str, Enum):
    """
    SAFEGUARD security levels determining approval requirements.

    L0: No approval needed (read-only, low risk)
    L1: Log only (audit trail, auto-approved)
    L2: Notification (inform + auto-approve after delay)
    L3: Human approval required (blocking)
    L4: Multi-approval required (critical operations)
    """
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class ApprovalStatus(str, Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ApprovalRequest(BaseModel):
    """
    SAFEGUARD approval request.

    Created when a workflow or MCP tool requires human validation.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Request metadata
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    safeguard_level: SafeguardLevel = SafeguardLevel.L3

    # Context
    workflow_name: Optional[str] = None
    workflow_id: Optional[str] = None
    caller_ip: Optional[str] = None
    caller_user: Optional[str] = None

    # AI reasoning (from LLM)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    risk_assessment: Optional[str] = None

    # Status tracking
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Resolution
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None

    # Execution result (after approval)
    execution_result: Optional[dict] = None
    execution_error: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def is_expired(self) -> bool:
        """Check if the request has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def can_be_approved(self) -> bool:
        """Check if request can still be approved"""
        return self.status == ApprovalStatus.PENDING and not self.is_expired()


class ApprovalResponse(BaseModel):
    """Response after approval/rejection"""
    request_id: str
    status: ApprovalStatus
    resolved_by: str
    resolution_note: Optional[str] = None
    execution_result: Optional[dict] = None
    execution_error: Optional[str] = None


class SafeguardNotification(BaseModel):
    """Notification to send for approval requests"""
    request: ApprovalRequest
    channel: str = "slack"  # slack, email, both
    approve_url: str
    reject_url: str
    dashboard_url: Optional[str] = None


class CreateApprovalRequest(BaseModel):
    """Request body for creating a new approval"""
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    safeguard_level: SafeguardLevel = SafeguardLevel.L3

    # Optional context
    workflow_name: Optional[str] = None
    workflow_id: Optional[str] = None

    # AI reasoning
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    risk_assessment: Optional[str] = None

    # Expiration
    expires_in_minutes: int = Field(default=60, ge=5, le=1440)


class ResolveApprovalRequest(BaseModel):
    """Request body for approving/rejecting"""
    resolved_by: str
    resolution_note: Optional[str] = None
