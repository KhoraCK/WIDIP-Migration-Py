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
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from workflows.core.config import settings
from workflows.core.mcp_client import MCPClient
from workflows.core.redis_client import RedisClient
from workflows.core.scheduler import WorkflowScheduler

# Import workflows
from workflows.health_check import HealthCheckWorkflow
from workflows.safeguard import (
    SafeguardCleanupWorkflow,
    SafeguardService,
    SafeguardNotifier,
    CreateApprovalRequest,
    ResolveApprovalRequest,
)

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
safeguard_service: SafeguardService = None
safeguard_notifier: SafeguardNotifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes clients and scheduler on startup.
    Cleans up on shutdown.
    """
    global mcp_client, redis_client, scheduler, safeguard_service, safeguard_notifier

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

    # Initialize SAFEGUARD service
    safeguard_service = SafeguardService(redis_client, mcp_client)
    safeguard_notifier = SafeguardNotifier(base_url="http://localhost:3002")

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

    # SAFEGUARD Cleanup - every hour
    scheduler.register_cron(
        SafeguardCleanupWorkflow,
        minute=0,  # At minute 0 of every hour
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


# ==================== SAFEGUARD Endpoints ====================


@app.post("/safeguard/request")
async def create_safeguard_request(
    request: CreateApprovalRequest,
    http_request: Request,
):
    """
    Create a new SAFEGUARD approval request.

    This is called by the MCP server when a tool requires human approval.
    """
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        approval = await safeguard_service.create_request(
            request,
            caller_ip=http_request.client.host if http_request.client else None,
        )

        # Send notification
        if safeguard_notifier:
            await safeguard_notifier.notify_approval_needed(approval, channels=["slack"])

        return {
            "success": True,
            "request_id": approval.id,
            "status": approval.status.value,
            "expires_at": approval.expires_at.isoformat() if approval.expires_at else None,
        }

    except Exception as e:
        logger.error("safeguard_create_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/safeguard/pending")
async def list_pending_approvals():
    """List all pending SAFEGUARD approval requests"""
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        pending = await safeguard_service.list_pending()
        return {
            "success": True,
            "count": len(pending),
            "requests": [
                {
                    "id": r.id,
                    "tool_name": r.tool_name,
                    "safeguard_level": r.safeguard_level.value,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "created_at": r.created_at.isoformat(),
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                    "workflow_name": r.workflow_name,
                }
                for r in pending
            ],
        }
    except Exception as e:
        logger.error("safeguard_list_pending_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/safeguard/request/{request_id}")
async def get_safeguard_request(request_id: str):
    """Get details of a specific approval request"""
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    request = await safeguard_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "success": True,
        "request": {
            "id": request.id,
            "tool_name": request.tool_name,
            "arguments": request.arguments,
            "safeguard_level": request.safeguard_level.value,
            "status": request.status.value,
            "confidence": request.confidence,
            "reasoning": request.reasoning,
            "risk_assessment": request.risk_assessment,
            "workflow_name": request.workflow_name,
            "workflow_id": request.workflow_id,
            "caller_ip": request.caller_ip,
            "created_at": request.created_at.isoformat(),
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None,
            "resolved_by": request.resolved_by,
            "resolution_note": request.resolution_note,
            "execution_result": request.execution_result,
            "execution_error": request.execution_error,
        },
    }


@app.post("/safeguard/approve/{request_id}")
async def approve_safeguard_request(
    request_id: str,
    body: ResolveApprovalRequest,
):
    """
    Approve a SAFEGUARD request and execute the MCP tool.

    The tool will be executed immediately after approval.
    """
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        response = await safeguard_service.approve(
            request_id,
            resolved_by=body.resolved_by,
            resolution_note=body.resolution_note,
        )

        # Send notification
        if safeguard_notifier:
            request = await safeguard_service.get_request(request_id)
            if request:
                await safeguard_notifier.notify_approved(request)

        return {
            "success": True,
            "request_id": response.request_id,
            "status": response.status.value,
            "execution_result": response.execution_result,
            "execution_error": response.execution_error,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("safeguard_approve_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/safeguard/approve/{request_id}")
async def approve_safeguard_request_simple(
    request_id: str,
    user: str = Query(default="admin", description="Username of approver"),
):
    """
    Simple GET endpoint for approving via link click.

    Used in Slack notifications for quick approval.
    """
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        response = await safeguard_service.approve(
            request_id,
            resolved_by=user,
            resolution_note="Approved via quick link",
        )

        # Send notification
        if safeguard_notifier:
            request = await safeguard_service.get_request(request_id)
            if request:
                await safeguard_notifier.notify_approved(request)

        # Return HTML for browser
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>SAFEGUARD - Approved</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>✅ Request Approved</h1>
                <p>Request <code>{request_id[:8]}</code> has been approved.</p>
                <p>Tool executed: <code>{response.execution_result is not None}</code></p>
                {f'<p style="color: red;">Error: {response.execution_error}</p>' if response.execution_error else ''}
                <a href="/safeguard/pending">View Pending Requests</a>
            </body>
            </html>
            """,
            status_code=200,
        )

    except ValueError as e:
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>SAFEGUARD - Error</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Error</h1>
                <p>{str(e)}</p>
                <a href="/safeguard/pending">View Pending Requests</a>
            </body>
            </html>
            """,
            status_code=400,
        )


@app.post("/safeguard/reject/{request_id}")
async def reject_safeguard_request(
    request_id: str,
    body: ResolveApprovalRequest,
):
    """Reject a SAFEGUARD request"""
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        response = await safeguard_service.reject(
            request_id,
            resolved_by=body.resolved_by,
            resolution_note=body.resolution_note,
        )

        # Send notification
        if safeguard_notifier:
            request = await safeguard_service.get_request(request_id)
            if request:
                await safeguard_notifier.notify_rejected(request)

        return {
            "success": True,
            "request_id": response.request_id,
            "status": response.status.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("safeguard_reject_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/safeguard/reject/{request_id}")
async def reject_safeguard_request_simple(
    request_id: str,
    user: str = Query(default="admin", description="Username of rejector"),
    reason: str = Query(default="", description="Rejection reason"),
):
    """
    Simple GET endpoint for rejecting via link click.

    Used in Slack notifications for quick rejection.
    """
    if not safeguard_service:
        raise HTTPException(status_code=503, detail="SAFEGUARD service not initialized")

    try:
        response = await safeguard_service.reject(
            request_id,
            resolved_by=user,
            resolution_note=reason or "Rejected via quick link",
        )

        # Send notification
        if safeguard_notifier:
            request = await safeguard_service.get_request(request_id)
            if request:
                await safeguard_notifier.notify_rejected(request)

        # Return HTML for browser
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>SAFEGUARD - Rejected</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Request Rejected</h1>
                <p>Request <code>{request_id[:8]}</code> has been rejected.</p>
                <a href="/safeguard/pending">View Pending Requests</a>
            </body>
            </html>
            """,
            status_code=200,
        )

    except ValueError as e:
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>SAFEGUARD - Error</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Error</h1>
                <p>{str(e)}</p>
                <a href="/safeguard/pending">View Pending Requests</a>
            </body>
            </html>
            """,
            status_code=400,
        )


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
