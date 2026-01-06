"""
Workflow Scheduler - APScheduler wrapper for cron and interval triggers
"""

from datetime import datetime
from typing import Callable, Dict, Optional, Type

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .base import WorkflowBase
from .mcp_client import MCPClient
from .redis_client import RedisClient

logger = structlog.get_logger()


class WorkflowScheduler:
    """
    Scheduler for WIDIP workflows.

    Handles:
    - Registering workflows with cron or interval triggers
    - Managing workflow instances
    - Starting/stopping the scheduler
    - Manual workflow triggering
    """

    def __init__(
        self,
        mcp_client: MCPClient = None,
        redis_client: RedisClient = None,
        db_client=None,
    ):
        """
        Initialize scheduler.

        Args:
            mcp_client: Shared MCP client instance
            redis_client: Shared Redis client instance
            db_client: Shared database client instance
        """
        self.mcp_client = mcp_client
        self.redis_client = redis_client
        self.db_client = db_client

        self._scheduler = AsyncIOScheduler()
        self._workflows: Dict[str, WorkflowBase] = {}
        self._webhook_handlers: Dict[str, WorkflowBase] = {}

    def register_interval(
        self,
        workflow_class: Type[WorkflowBase],
        seconds: int = None,
        minutes: int = None,
        hours: int = None,
        **kwargs,
    ) -> WorkflowBase:
        """
        Register a workflow with interval trigger.

        Args:
            workflow_class: Workflow class to instantiate
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            **kwargs: Additional trigger arguments

        Returns:
            Workflow instance
        """
        workflow = self._create_workflow(workflow_class)

        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            **kwargs,
        )

        self._scheduler.add_job(
            self._run_workflow,
            trigger=trigger,
            id=workflow.name,
            name=f"Workflow: {workflow.name}",
            args=[workflow],
            replace_existing=True,
        )

        self._workflows[workflow.name] = workflow

        logger.info(
            "workflow_registered",
            workflow=workflow.name,
            trigger_type="interval",
            seconds=seconds,
            minutes=minutes,
            hours=hours,
        )

        return workflow

    def register_cron(
        self,
        workflow_class: Type[WorkflowBase],
        hour: int = None,
        minute: int = None,
        second: int = 0,
        day: str = None,
        day_of_week: str = None,
        **kwargs,
    ) -> WorkflowBase:
        """
        Register a workflow with cron trigger.

        Args:
            workflow_class: Workflow class to instantiate
            hour: Hour (0-23)
            minute: Minute (0-59)
            second: Second (0-59)
            day: Day of month
            day_of_week: Day of week (mon-sun)
            **kwargs: Additional trigger arguments

        Returns:
            Workflow instance
        """
        workflow = self._create_workflow(workflow_class)

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            second=second,
            day=day,
            day_of_week=day_of_week,
            **kwargs,
        )

        self._scheduler.add_job(
            self._run_workflow,
            trigger=trigger,
            id=workflow.name,
            name=f"Workflow: {workflow.name}",
            args=[workflow],
            replace_existing=True,
        )

        self._workflows[workflow.name] = workflow

        logger.info(
            "workflow_registered",
            workflow=workflow.name,
            trigger_type="cron",
            hour=hour,
            minute=minute,
        )

        return workflow

    def register_webhook(
        self,
        workflow_class: Type[WorkflowBase],
        path: str,
    ) -> WorkflowBase:
        """
        Register a workflow with webhook trigger.

        Note: The actual webhook endpoint must be created in FastAPI.
        This just registers the workflow for manual triggering.

        Args:
            workflow_class: Workflow class to instantiate
            path: Webhook path (for reference)

        Returns:
            Workflow instance
        """
        workflow = self._create_workflow(workflow_class)

        self._workflows[workflow.name] = workflow
        self._webhook_handlers[path] = workflow

        logger.info(
            "workflow_registered",
            workflow=workflow.name,
            trigger_type="webhook",
            path=path,
        )

        return workflow

    def _create_workflow(self, workflow_class: Type[WorkflowBase]) -> WorkflowBase:
        """Create workflow instance with shared clients"""
        return workflow_class(
            mcp_client=self.mcp_client,
            redis_client=self.redis_client,
            db_client=self.db_client,
        )

    async def _run_workflow(
        self,
        workflow: WorkflowBase,
        trigger_data: dict = None,
    ) -> dict:
        """
        Run a workflow (called by scheduler or manually).

        Args:
            workflow: Workflow instance
            trigger_data: Optional trigger data

        Returns:
            Workflow result
        """
        return await workflow.run(
            trigger_data=trigger_data,
            trigger_type="cron",
        )

    async def trigger(
        self,
        workflow_name: str,
        trigger_data: dict = None,
        trigger_type: str = "manual",
        caller_ip: str = None,
        caller_user: str = None,
    ) -> dict:
        """
        Manually trigger a workflow.

        Args:
            workflow_name: Name of the workflow to trigger
            trigger_data: Input data
            trigger_type: Type of trigger
            caller_ip: Caller IP address
            caller_user: Caller username

        Returns:
            Workflow result
        """
        workflow = self._workflows.get(workflow_name)

        if not workflow:
            logger.error("workflow_not_found", workflow=workflow_name)
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_name}",
            }

        return await workflow.run(
            trigger_data=trigger_data,
            trigger_type=trigger_type,
            caller_ip=caller_ip,
            caller_user=caller_user,
        )

    async def trigger_webhook(
        self,
        path: str,
        trigger_data: dict = None,
        caller_ip: str = None,
    ) -> dict:
        """
        Trigger workflow registered for a webhook path.

        Args:
            path: Webhook path
            trigger_data: Input data
            caller_ip: Caller IP address

        Returns:
            Workflow result
        """
        workflow = self._webhook_handlers.get(path)

        if not workflow:
            logger.error("webhook_handler_not_found", path=path)
            return {
                "success": False,
                "error": f"No workflow registered for path: {path}",
            }

        return await workflow.run(
            trigger_data=trigger_data,
            trigger_type="webhook",
            caller_ip=caller_ip,
        )

    def get_workflow(self, name: str) -> Optional[WorkflowBase]:
        """Get a workflow by name"""
        return self._workflows.get(name)

    def list_workflows(self) -> list:
        """List all registered workflows"""
        return [
            {
                "name": w.name,
                "description": w.description,
                "status": w.status.value,
                "safeguard_level": w.safeguard_level,
            }
            for w in self._workflows.values()
        ]

    def list_jobs(self) -> list:
        """List all scheduled jobs"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in self._scheduler.get_jobs()
        ]

    def start(self) -> None:
        """Start the scheduler"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info(
                "scheduler_started",
                workflows=list(self._workflows.keys()),
                jobs=len(self._scheduler.get_jobs()),
            )

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.

        Args:
            wait: Wait for running jobs to complete
        """
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("scheduler_stopped")

    def pause_job(self, workflow_name: str) -> bool:
        """Pause a scheduled job"""
        try:
            self._scheduler.pause_job(workflow_name)
            logger.info("job_paused", workflow=workflow_name)
            return True
        except Exception as e:
            logger.error("job_pause_failed", workflow=workflow_name, error=str(e))
            return False

    def resume_job(self, workflow_name: str) -> bool:
        """Resume a paused job"""
        try:
            self._scheduler.resume_job(workflow_name)
            logger.info("job_resumed", workflow=workflow_name)
            return True
        except Exception as e:
            logger.error("job_resume_failed", workflow=workflow_name, error=str(e))
            return False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._scheduler.running
