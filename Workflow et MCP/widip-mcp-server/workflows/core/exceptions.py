"""
Custom exceptions for WIDIP workflows
"""


class WorkflowError(Exception):
    """Base exception for all workflow errors"""

    def __init__(self, message: str, workflow_name: str = None, details: dict = None):
        self.message = message
        self.workflow_name = workflow_name
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "workflow": self.workflow_name,
            "details": self.details,
        }


class WorkflowTimeoutError(WorkflowError):
    """Raised when a workflow exceeds its timeout"""

    def __init__(
        self,
        message: str = "Workflow timeout exceeded",
        workflow_name: str = None,
        timeout_seconds: int = None,
    ):
        super().__init__(
            message, workflow_name, {"timeout_seconds": timeout_seconds}
        )
        self.timeout_seconds = timeout_seconds


class WorkflowValidationError(WorkflowError):
    """Raised when workflow input validation fails"""

    def __init__(
        self,
        message: str = "Validation error",
        workflow_name: str = None,
        field: str = None,
        value: any = None,
    ):
        super().__init__(
            message, workflow_name, {"field": field, "invalid_value": str(value)}
        )
        self.field = field
        self.value = value


class MCPError(WorkflowError):
    """Raised when MCP Server call fails"""

    def __init__(
        self,
        message: str,
        tool_name: str = None,
        error_code: int = None,
        mcp_response: dict = None,
    ):
        super().__init__(
            message,
            details={
                "tool_name": tool_name,
                "error_code": error_code,
                "mcp_response": mcp_response,
            },
        )
        self.tool_name = tool_name
        self.error_code = error_code
        self.mcp_response = mcp_response


class SafeguardBlockedError(WorkflowError):
    """Raised when SAFEGUARD blocks an action (L3+ required)"""

    def __init__(
        self,
        message: str = "Action blocked by SAFEGUARD - human approval required",
        tool_name: str = None,
        security_level: str = None,
        approval_id: str = None,
    ):
        super().__init__(
            message,
            details={
                "tool_name": tool_name,
                "security_level": security_level,
                "approval_id": approval_id,
            },
        )
        self.tool_name = tool_name
        self.security_level = security_level
        self.approval_id = approval_id


class CircuitBreakerOpenError(WorkflowError):
    """Raised when circuit breaker is open (service unavailable)"""

    def __init__(
        self,
        message: str = "Circuit breaker is open",
        service_name: str = None,
    ):
        super().__init__(message, details={"service_name": service_name})
        self.service_name = service_name


class RetryExhaustedError(WorkflowError):
    """Raised when all retry attempts have been exhausted"""

    def __init__(
        self,
        message: str = "All retry attempts exhausted",
        attempts: int = None,
        last_error: Exception = None,
    ):
        super().__init__(
            message,
            details={
                "attempts": attempts,
                "last_error": str(last_error) if last_error else None,
            },
        )
        self.attempts = attempts
        self.last_error = last_error
