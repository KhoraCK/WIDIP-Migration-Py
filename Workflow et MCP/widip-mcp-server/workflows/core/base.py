"""
Base workflow class - all workflows inherit from this
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import structlog

from .context import WorkflowContext
from .exceptions import WorkflowError, WorkflowTimeoutError

logger = structlog.get_logger()


class WorkflowStatus(str, Enum):
    """Workflow execution status"""

    IDLE = "idle"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class WorkflowBase(ABC):
    """
    Abstract base class for all WIDIP workflows.

    Subclasses must implement:
    - execute(ctx: WorkflowContext) -> Any

    Optional overrides:
    - validate(trigger_data: dict) -> bool
    - on_success(ctx: WorkflowContext, result: Any) -> None
    - on_error(ctx: WorkflowContext, error: Exception) -> None
    """

    # Workflow identifier (override in subclass)
    name: str = "base"

    # Default timeout in seconds
    timeout_seconds: int = 60

    # SAFEGUARD level for this workflow (L0-L4)
    safeguard_level: str = "L0"

    # Description for logging
    description: str = "Base workflow"

    def __init__(
        self,
        mcp_client=None,
        redis_client=None,
        db_client=None,
    ):
        """
        Initialize workflow with required clients.

        Args:
            mcp_client: MCPClient instance for tool calls
            redis_client: RedisClient instance for cache/state
            db_client: Database client for PostgreSQL
        """
        self.mcp = mcp_client
        self.redis = redis_client
        self.db = db_client
        self.status = WorkflowStatus.IDLE
        self._current_context: Optional[WorkflowContext] = None

    async def run(
        self,
        trigger_data: dict = None,
        trigger_type: str = "manual",
        caller_ip: str = None,
        caller_user: str = None,
    ) -> dict:
        """
        Main entry point to run the workflow.

        Args:
            trigger_data: Input data from trigger
            trigger_type: Type of trigger ('webhook', 'cron', 'manual')
            caller_ip: IP address of caller (for audit)
            caller_user: Username of caller (for audit)

        Returns:
            dict with success status, result or error
        """
        # Create execution context
        ctx = WorkflowContext(
            workflow_name=self.name,
            trigger_data=trigger_data or {},
            trigger_type=trigger_type,
            caller_ip=caller_ip,
            caller_user=caller_user,
        )
        self._current_context = ctx

        logger.info(
            "workflow_started",
            workflow=self.name,
            workflow_id=ctx.workflow_id,
            trigger_type=trigger_type,
        )

        try:
            # Validate input
            if not await self.validate(trigger_data or {}):
                raise WorkflowError(
                    "Validation failed",
                    workflow_name=self.name,
                )

            # Set status
            self.status = WorkflowStatus.RUNNING

            # Execute with timeout
            result = await asyncio.wait_for(
                self.execute(ctx),
                timeout=self.timeout_seconds,
            )

            # Mark complete
            ctx.complete()
            self.status = WorkflowStatus.COMPLETED

            # Success callback
            await self.on_success(ctx, result)

            logger.info(
                "workflow_completed",
                workflow=self.name,
                workflow_id=ctx.workflow_id,
                elapsed_ms=ctx.elapsed_ms,
                tools_called=len(ctx.tools_called),
            )

            return {
                "success": True,
                "workflow_id": ctx.workflow_id,
                "result": result,
                "elapsed_ms": ctx.elapsed_ms,
                "tools_called": len(ctx.tools_called),
            }

        except asyncio.TimeoutError:
            ctx.complete()
            self.status = WorkflowStatus.TIMEOUT
            error = WorkflowTimeoutError(
                f"Workflow {self.name} exceeded timeout of {self.timeout_seconds}s",
                workflow_name=self.name,
                timeout_seconds=self.timeout_seconds,
            )
            ctx.add_error(str(error))
            await self.on_error(ctx, error)

            logger.error(
                "workflow_timeout",
                workflow=self.name,
                workflow_id=ctx.workflow_id,
                timeout_seconds=self.timeout_seconds,
            )

            return {
                "success": False,
                "workflow_id": ctx.workflow_id,
                "error": error.to_dict(),
                "elapsed_ms": ctx.elapsed_ms,
            }

        except WorkflowError as e:
            ctx.complete()
            self.status = WorkflowStatus.FAILED
            ctx.add_error(str(e), e.details)
            await self.on_error(ctx, e)

            logger.error(
                "workflow_error",
                workflow=self.name,
                workflow_id=ctx.workflow_id,
                error=str(e),
                error_type=e.__class__.__name__,
            )

            return {
                "success": False,
                "workflow_id": ctx.workflow_id,
                "error": e.to_dict(),
                "elapsed_ms": ctx.elapsed_ms,
            }

        except Exception as e:
            ctx.complete()
            self.status = WorkflowStatus.FAILED
            ctx.add_error(str(e))
            await self.on_error(ctx, e)

            logger.exception(
                "workflow_unexpected_error",
                workflow=self.name,
                workflow_id=ctx.workflow_id,
                error=str(e),
            )

            return {
                "success": False,
                "workflow_id": ctx.workflow_id,
                "error": {
                    "error": "UnexpectedError",
                    "message": str(e),
                    "workflow": self.name,
                },
                "elapsed_ms": ctx.elapsed_ms,
            }

        finally:
            self._current_context = None

    @abstractmethod
    async def execute(self, ctx: WorkflowContext) -> Any:
        """
        Main workflow logic - must be implemented by subclass.

        Args:
            ctx: WorkflowContext with trigger data and state

        Returns:
            Workflow result (any type)
        """
        pass

    async def validate(self, trigger_data: dict) -> bool:
        """
        Validate trigger data before execution.
        Override in subclass for custom validation.

        Args:
            trigger_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        return True

    async def on_success(self, ctx: WorkflowContext, result: Any) -> None:
        """
        Called after successful execution.
        Override for custom success handling (notifications, logging).

        Args:
            ctx: Execution context
            result: Workflow result
        """
        pass

    async def on_error(self, ctx: WorkflowContext, error: Exception) -> None:
        """
        Called after failed execution.
        Override for custom error handling (alerts, cleanup).

        Args:
            ctx: Execution context
            error: The exception that occurred
        """
        pass

    async def call_mcp(
        self,
        tool_name: str,
        arguments: dict,
        ctx: WorkflowContext = None,
    ) -> dict:
        """
        Helper to call MCP tool with logging.

        Args:
            tool_name: Name of the MCP tool
            arguments: Tool arguments
            ctx: Optional context for logging

        Returns:
            Tool result
        """
        if not self.mcp:
            raise WorkflowError(
                "MCP client not configured",
                workflow_name=self.name,
            )

        context = ctx or self._current_context
        start_time = datetime.utcnow()

        try:
            result = await self.mcp.call(tool_name, arguments)

            duration_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            if context:
                context.log_tool_call(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    success=True,
                    duration_ms=duration_ms,
                )

            return result

        except Exception as e:
            duration_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            if context:
                context.log_tool_call(
                    tool_name=tool_name,
                    arguments=arguments,
                    success=False,
                    duration_ms=duration_ms,
                )

            raise

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self.status.value}>"
