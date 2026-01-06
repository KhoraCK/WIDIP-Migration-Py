"""
WIDIP Workflow Runner

Main entry point for running Python workflows.
Starts FastAPI server with scheduler.

Usage:
    python -m workflows.runner

Or with uvicorn:
    uvicorn workflows.runner:app --host 0.0.0.0 --port 3002
"""

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from workflows.core.config import settings
from workflows.core.mcp_client import MCPClient
from workflows.core.redis_client import RedisClient
from workflows.core.scheduler import WorkflowScheduler

# Import workflows
from workflows.health_check import HealthCheckWorkflow

# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
        if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
mcp_client: MCPClient = None
redis_client: RedisClient = None
scheduler: WorkflowScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes clients and scheduler on startup.
    Cleans up on shutdown.
    """
    global mcp_client, redis_client, scheduler

    logger.info(
        "workflow_runner_starting",
        environment=settings.environment,
        mcp_server=settings.mcp_server_url,
        redis=settings.redis_url,
    )

    # Initialize clients
    mcp_client = MCPClient(
        base_url=settings.mcp_server_url,
        api_key=settings.get_mcp_api_key(),
        timeout_seconds=settings.mcp_timeout_seconds,
        max_retries=settings.mcp_max_retries,
    )

    redis_client = RedisClient(
        url=settings.redis_url,
        db=settings.redis_db,
    )

    # Test Redis connection
    if await redis_client.ping():
        logger.info("redis_connected")
    else:
        logger.warning("redis_connection_failed")

    # Initialize scheduler
    scheduler = WorkflowScheduler(
        mcp_client=mcp_client,
        redis_client=redis_client,
    )

    # Register workflows
    if settings.scheduler_enabled:
        _register_workflows()
        scheduler.start()
        logger.info(
            "scheduler_started",
            workflows=len(scheduler.list_workflows()),
            jobs=len(scheduler.list_jobs()),
        )

    yield

    # Shutdown
    logger.info("workflow_runner_stopping")

    if scheduler:
        scheduler.shutdown(wait=True)

    if redis_client:
        await redis_client.close()

    if mcp_client:
        await mcp_client.close()

    logger.info("workflow_runner_stopped")


def _register_workflows():
    """Register all workflows with the scheduler"""

    # Health Check - every 30 seconds
    scheduler.register_interval(
        HealthCheckWorkflow,
        seconds=settings.health_check_interval_seconds,
    )

    # TODO: Register other workflows as they are migrated
    # scheduler.register_interval(
    #     SupportWorkflow,
    #     minutes=settings.support_polling_interval_minutes,
    # )
    #
    # scheduler.register_cron(
    #     EnrichisseurWorkflow,
    #     hour=settings.enrichisseur_hour,
    #     minute=settings.enrichisseur_minute,
    # )
    #
    # scheduler.register_webhook(
    #     SentinelWorkflow,
    #     path="/webhook/observium",
    # )


# Create FastAPI app
app = FastAPI(
    title="WIDIP Workflow Runner",
    description="Python workflow engine for WIDIP",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API Endpoints ====================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = await redis_client.ping() if redis_client else False
    mcp_health = await mcp_client.health_check() if mcp_client else {"status": "unknown"}

    glpi_status = await redis_client.get_health_status("glpi") if redis_client else "unknown"

    return {
        "status": "healthy" if redis_ok else "degraded",
        "services": {
            "redis": "ok" if redis_ok else "down",
            "mcp_server": mcp_health.get("status", "unknown"),
            "glpi": glpi_status,
        },
        "scheduler": {
            "running": scheduler.is_running if scheduler else False,
            "workflows": len(scheduler.list_workflows()) if scheduler else 0,
            "jobs": len(scheduler.list_jobs()) if scheduler else 0,
        },
    }


@app.get("/workflows")
async def list_workflows():
    """List all registered workflows"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    return {
        "workflows": scheduler.list_workflows(),
        "jobs": scheduler.list_jobs(),
    }


@app.post("/workflows/{workflow_name}/trigger")
async def trigger_workflow(
    workflow_name: str,
    request: Request,
):
    """Manually trigger a workflow"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        body = await request.json()
    except Exception:
        body = {}

    result = await scheduler.trigger(
        workflow_name=workflow_name,
        trigger_data=body,
        trigger_type="manual",
        caller_ip=request.client.host if request.client else None,
    )

    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    return result


@app.post("/webhook/observium")
async def observium_webhook(request: Request):
    """Webhook endpoint for Observium alerts (SENTINEL)"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await scheduler.trigger_webhook(
        path="/webhook/observium",
        trigger_data=body,
        caller_ip=request.client.host if request.client else None,
    )

    # Return immediately with tracking ID (async processing)
    return {
        "received": True,
        "workflow_id": result.get("workflow_id"),
    }


@app.post("/scheduler/pause/{workflow_name}")
async def pause_workflow(workflow_name: str):
    """Pause a scheduled workflow"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    success = scheduler.pause_job(workflow_name)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"status": "paused", "workflow": workflow_name}


@app.post("/scheduler/resume/{workflow_name}")
async def resume_workflow(workflow_name: str):
    """Resume a paused workflow"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    success = scheduler.resume_job(workflow_name)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"status": "resumed", "workflow": workflow_name}


# ==================== Main ====================


def main():
    """Run the workflow server"""
    import uvicorn

    uvicorn.run(
        "workflows.runner:app",
        host="0.0.0.0",
        port=3002,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
