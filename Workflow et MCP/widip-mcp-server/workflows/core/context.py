"""
Workflow execution context
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class WorkflowContext:
    """
    Context object passed through workflow execution.
    Contains trigger data, state, and execution metadata.
    """

    # Unique execution ID
    workflow_id: str = field(default_factory=lambda: uuid4().hex[:12])

    # Workflow name
    workflow_name: str = ""

    # Input data from trigger (webhook, cron, manual)
    trigger_data: dict = field(default_factory=dict)

    # Trigger type: 'webhook', 'cron', 'manual'
    trigger_type: str = "manual"

    # Mutable state during execution
    state: dict = field(default_factory=dict)

    # Execution timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Caller information
    caller_ip: Optional[str] = None
    caller_user: Optional[str] = None

    # Execution metadata
    metadata: dict = field(default_factory=dict)

    # Errors encountered
    errors: list = field(default_factory=list)

    # Tools called during execution (for audit)
    tools_called: list = field(default_factory=list)

    @property
    def elapsed_ms(self) -> int:
        """Time elapsed since start in milliseconds"""
        end = self.completed_at or datetime.utcnow()
        return int((end - self.started_at).total_seconds() * 1000)

    @property
    def elapsed_seconds(self) -> float:
        """Time elapsed since start in seconds"""
        return self.elapsed_ms / 1000

    def set_state(self, key: str, value: Any) -> None:
        """Set a state value"""
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        return self.state.get(key, default)

    def add_error(self, error: str, details: dict = None) -> None:
        """Record an error"""
        self.errors.append({
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        result: Any = None,
        success: bool = True,
        duration_ms: int = 0,
    ) -> None:
        """Log a tool call for audit"""
        self.tools_called.append({
            "tool_name": tool_name,
            "arguments": self._redact_sensitive(arguments),
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def _redact_sensitive(self, data: dict) -> dict:
        """Redact sensitive fields from arguments"""
        sensitive_keys = {"password", "secret", "token", "api_key", "apikey"}
        redacted = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive(value)
            else:
                redacted[key] = value
        return redacted

    def complete(self) -> None:
        """Mark execution as complete"""
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "trigger_type": self.trigger_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_ms": self.elapsed_ms,
            "state": self.state,
            "errors": self.errors,
            "tools_called": self.tools_called,
            "metadata": self.metadata,
        }

    def to_log_dict(self) -> dict:
        """Minimal dict for structured logging"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "trigger_type": self.trigger_type,
            "elapsed_ms": self.elapsed_ms,
            "tools_count": len(self.tools_called),
            "errors_count": len(self.errors),
        }
