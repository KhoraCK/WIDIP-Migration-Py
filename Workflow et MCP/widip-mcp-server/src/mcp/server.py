"""
Serveur MCP FastAPI avec support SSE.

Ce module expose les endpoints MCP pour n8n 2.0:
- GET /mcp/sse : Endpoint SSE pour la découverte des tools
- POST /mcp/call : Endpoint pour l'exécution des tools
- GET /health : Health check

SAFEGUARD: Niveaux de sécurité L0-L4 intégrés
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from sse_starlette.sse import EventSourceResponse

from ..config import (
    SecurityLevel,
    TOOL_SECURITY_LEVELS,
    get_settings,
)
from ..clients.memory import memory_client
from .protocol import ExecutionContext, MCPErrorCode, MCPRequest, MCPResponse
from .registry import tool_registry
from .safeguard_queue import safeguard_queue, ApprovalStatus

logger = structlog.get_logger(__name__)

# =============================================================================
# Security - API Key Authentication
# =============================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Vérifie la clé API pour les requêtes authentifiées.

    En mode développement (mcp_require_auth=False), l'authentification est optionnelle.
    """
    settings = get_settings()

    # Si l'auth n'est pas requise, accepter toutes les requêtes
    if not settings.mcp_require_auth:
        return None

    # Si l'API key n'est pas configurée, désactiver l'auth
    if not settings.mcp_api_key.get_secret_value():
        logger.warning("mcp_api_key_not_configured", action="auth_disabled")
        return None

    # Vérifier la clé
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Provide X-API-Key header.",
        )

    if api_key != settings.mcp_api_key.get_secret_value():
        logger.warning("mcp_invalid_api_key", provided_key=api_key[:8] + "...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key",
        )

    return api_key


# =============================================================================
# SAFEGUARD - Vérification des niveaux de sécurité
# =============================================================================


class SafeguardResponse:
    """Réponse de validation SAFEGUARD."""

    def __init__(
        self,
        allowed: bool,
        level: SecurityLevel,
        message: str,
        requires_human: bool = False,
        pending_approval_id: Optional[str] = None,
    ):
        self.allowed = allowed
        self.level = level
        self.message = message
        self.requires_human = requires_human
        self.pending_approval_id = pending_approval_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "level": self.level.value,
            "message": self.message,
            "requires_human": self.requires_human,
            "pending_approval_id": self.pending_approval_id,
        }


def check_safeguard(
    tool_name: str,
    confidence: float = 100.0,
) -> SafeguardResponse:
    """
    Vérifie si un tool peut être exécuté selon les règles SAFEGUARD.

    Args:
        tool_name: Nom du tool MCP
        confidence: Niveau de confiance de l'IA (0-100)

    Returns:
        SafeguardResponse avec la décision
    """
    settings = get_settings()

    # SAFEGUARD désactivé = tout est permis
    if not settings.safeguard_enabled:
        return SafeguardResponse(
            allowed=True,
            level=SecurityLevel.L0_READ_ONLY,
            message="SAFEGUARD disabled",
        )

    # Récupérer le niveau du tool (L0 par défaut si non défini)
    level = TOOL_SECURITY_LEVELS.get(tool_name, SecurityLevel.L0_READ_ONLY)

    # L0: Lecture seule - toujours autorisé
    if level == SecurityLevel.L0_READ_ONLY:
        return SafeguardResponse(
            allowed=True,
            level=level,
            message="Action en lecture seule autorisée",
        )

    # L1: Actions mineures - autorisé si confidence >= 80%
    if level == SecurityLevel.L1_MINOR:
        if confidence >= 80.0:
            return SafeguardResponse(
                allowed=True,
                level=level,
                message=f"Action mineure autorisée (confidence: {confidence}%)",
            )
        return SafeguardResponse(
            allowed=False,
            level=level,
            message=f"Confidence insuffisante ({confidence}% < 80%). Validation requise.",
            requires_human=True,
        )

    # L2: Actions modérées - autorisé avec notification
    if level == SecurityLevel.L2_MODERATE:
        # On autorise mais on log pour notification
        logger.warning(
            "safeguard_l2_action",
            tool=tool_name,
            confidence=confidence,
            action="executing_with_notification",
        )
        return SafeguardResponse(
            allowed=True,
            level=level,
            message=f"Action modérée exécutée (notification envoyée)",
        )

    # L3: Actions sensibles - VALIDATION HUMAINE OBLIGATOIRE
    # Note: L'ID d'approbation est généré lors de la création de la demande
    if level == SecurityLevel.L3_SENSITIVE:
        logger.warning(
            "safeguard_l3_requires_approval",
            tool=tool_name,
            action="human_validation_required",
        )
        return SafeguardResponse(
            allowed=False,
            level=level,
            message=f"ACTION SENSIBLE BLOQUÉE. Validation humaine requise. "
                    f"Utilisez POST /safeguard/request pour soumettre une demande.",
            requires_human=True,
            pending_approval_id=None,
        )

    # L4: Actions interdites - JAMAIS exécutées par l'IA
    if level == SecurityLevel.L4_FORBIDDEN:
        logger.error(
            "safeguard_l4_forbidden",
            tool=tool_name,
            action="blocked_permanently",
        )
        return SafeguardResponse(
            allowed=False,
            level=level,
            message=f"ACTION INTERDITE. Ce tool ne peut être exécuté que manuellement par un humain.",
            requires_human=True,
        )

    # Fallback: refuser par sécurité
    return SafeguardResponse(
        allowed=False,
        level=level,
        message="Niveau de sécurité inconnu - action refusée par précaution",
        requires_human=True,
    )


# =============================================================================
# Lifespan (startup/shutdown)
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestion du cycle de vie de l'application."""
    settings = get_settings()

    # ==========================================================================
    # VALIDATION DE SÉCURITÉ AU DÉMARRAGE
    # ==========================================================================
    security_errors = settings.validate_security()
    for error in security_errors:
        if error.startswith("CRITICAL"):
            logger.error("security_validation_failed", error=error)
            raise RuntimeError(error)
        else:
            logger.warning("security_validation_warning", warning=error)

    # ==========================================================================
    # INITIALISATION DU POOL DE CONNEXIONS ET DE LA QUEUE SAFEGUARD
    # ==========================================================================
    try:
        # Initialiser le pool PostgreSQL au démarrage
        await memory_client._get_pool()
        logger.info("database_pool_initialized")

        # Initialiser la queue SAFEGUARD (crée la table si nécessaire)
        await safeguard_queue.initialize()
        logger.info("safeguard_queue_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        # On continue quand même, les pools seront créés à la demande

    # Startup
    logger.info(
        "mcp_server_starting",
        tools_count=len(tool_registry),
        tools=list(tool_registry._tools.keys()),
        safeguard_enabled=settings.safeguard_enabled,
        auth_required=settings.mcp_require_auth,
        api_key_configured=bool(settings.mcp_api_key.get_secret_value()),
    )
    yield

    # ==========================================================================
    # CLEANUP
    # ==========================================================================
    logger.info("mcp_server_stopping")
    await memory_client.close()
    await safeguard_queue.close()
    logger.info("database_pools_closed")


# =============================================================================
# Application Factory
# =============================================================================


def create_mcp_app() -> FastAPI:
    """
    Crée et configure l'application FastAPI MCP.

    Returns:
        FastAPI: Application configurée
    """
    settings = get_settings()

    app = FastAPI(
        title="WIDIP MCP Server",
        description="Serveur MCP centralisé pour WIDIP - Intégration GLPI, Observium, AD, SMTP. SAFEGUARD L0-L4 activé.",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS sécurisé - utiliser les origins configurées
    allowed_origins = [
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ]

    # Fallback si aucune origin configurée
    if not allowed_origins:
        allowed_origins = ["http://localhost:5678", "http://127.0.0.1:5678"]
        logger.warning("cors_fallback_origins", origins=allowed_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    logger.info("cors_configured", allowed_origins=allowed_origins)

    # Enregistrer les routes
    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Enregistre les routes MCP."""

    settings = get_settings()

    # -------------------------------------------------------------------------
    # Health Check (pas d'auth requise)
    # -------------------------------------------------------------------------

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """
        Health check endpoint avec vérification des dépendances.

        Retourne:
        - healthy: Tout fonctionne
        - degraded: Certaines dépendances sont down mais le service peut fonctionner
        - unhealthy: Le service ne peut pas fonctionner
        """
        checks = {}

        # Check PostgreSQL
        try:
            import asyncpg
            conn = await asyncpg.connect(settings.postgres_dsn, timeout=5.0)
            await conn.execute("SELECT 1")
            await conn.close()
            checks["postgresql"] = {"status": "ok", "latency_ms": None}
        except Exception as e:
            checks["postgresql"] = {"status": "error", "error": str(e)[:100]}

        # Check Redis
        try:
            import redis.asyncio as aioredis
            redis_client = aioredis.from_url(settings.redis_url, socket_timeout=5.0)
            await redis_client.ping()
            await redis_client.close()
            checks["redis"] = {"status": "ok"}
        except Exception as e:
            checks["redis"] = {"status": "error", "error": str(e)[:100]}

        # Check GLPI (si configuré)
        if settings.glpi_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{settings.glpi_url}/apirest.php/")
                    checks["glpi"] = {
                        "status": "ok" if resp.status_code < 500 else "error",
                        "http_code": resp.status_code
                    }
            except Exception as e:
                checks["glpi"] = {"status": "error", "error": str(e)[:100]}
        else:
            checks["glpi"] = {"status": "not_configured"}

        # Check Observium (si configuré)
        if settings.observium_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{settings.observium_url}/api/v0/devices",
                        auth=(settings.observium_user, settings.observium_pass.get_secret_value())
                    )
                    checks["observium"] = {
                        "status": "ok" if resp.status_code < 500 else "error",
                        "http_code": resp.status_code
                    }
            except Exception as e:
                checks["observium"] = {"status": "error", "error": str(e)[:100]}
        else:
            checks["observium"] = {"status": "not_configured"}

        # Déterminer le statut global
        critical_checks = ["postgresql"]  # Redis optionnel pour fonctionner
        critical_errors = [k for k in critical_checks if checks.get(k, {}).get("status") == "error"]
        all_errors = [k for k, v in checks.items() if v.get("status") == "error"]

        if critical_errors:
            status = "unhealthy"
            http_code = 503
        elif all_errors:
            status = "degraded"
            http_code = 200  # On reste up, mais on signale le problème
        else:
            status = "healthy"
            http_code = 200

        response = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "tools_count": len(tool_registry),
            "safeguard_enabled": settings.safeguard_enabled,
            "checks": checks,
        }

        if status != "healthy":
            logger.warning("health_check_degraded", status=status, checks=checks)

        return JSONResponse(content=response, status_code=http_code)

    # -------------------------------------------------------------------------
    # MCP SSE Endpoint (Découverte des tools)
    # -------------------------------------------------------------------------

    @app.get("/mcp/sse")
    async def mcp_sse_endpoint(
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> EventSourceResponse:
        """
        Endpoint SSE pour la découverte des tools MCP.

        n8n MCP Client se connecte à cet endpoint pour:
        1. Recevoir la liste des tools disponibles
        2. Maintenir une connexion pour les mises à jour (optionnel)
        """

        async def event_generator() -> AsyncGenerator[dict[str, str], None]:
            client_ip = request.client.host if request.client else "unknown"
            logger.info("mcp_sse_connection", client_ip=client_ip)

            # Envoyer la liste des tools avec leurs niveaux de sécurité
            tools_schemas = tool_registry.get_schemas()

            # Enrichir les schemas avec les niveaux SAFEGUARD
            for tool in tools_schemas:
                tool_name = tool.get("name", "")
                level = TOOL_SECURITY_LEVELS.get(tool_name, SecurityLevel.L0_READ_ONLY)
                tool["security_level"] = level.value

            yield {
                "event": "tools",
                "data": json.dumps(tools_schemas),
            }

            logger.info(
                "mcp_sse_tools_sent",
                client_ip=client_ip,
                tools_count=len(tools_schemas),
            )

            # Maintenir la connexion ouverte avec des heartbeats
            try:
                while True:
                    if await request.is_disconnected():
                        logger.info("mcp_sse_client_disconnected", client_ip=client_ip)
                        break

                    # Heartbeat toutes les 30 secondes
                    await asyncio.sleep(30)
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": datetime.utcnow().isoformat()}),
                    }

            except asyncio.CancelledError:
                logger.info("mcp_sse_connection_cancelled", client_ip=client_ip)

        return EventSourceResponse(event_generator())

    # -------------------------------------------------------------------------
    # MCP Call Endpoint (Exécution des tools)
    # -------------------------------------------------------------------------

    @app.post("/mcp/call")
    async def mcp_call_endpoint(
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Endpoint pour l'exécution des tools MCP.

        Reçoit une requête JSON-RPC et exécute le tool demandé.
        SAFEGUARD: Vérifie les niveaux de sécurité avant exécution.
        """
        try:
            body = await request.json()
        except Exception as e:
            logger.warning("mcp_call_invalid_json", error=str(e))
            return JSONResponse(
                content=MCPResponse.failure(
                    request_id="unknown",
                    code=MCPErrorCode.PARSE_ERROR,
                    message="Invalid JSON",
                ).model_dump(),
                status_code=400,
            )

        # Parser la requête MCP
        try:
            mcp_request = MCPRequest(**body)
        except Exception as e:
            logger.warning("mcp_call_invalid_request", error=str(e))
            return JSONResponse(
                content=MCPResponse.failure(
                    request_id=body.get("id", "unknown"),
                    code=MCPErrorCode.INVALID_REQUEST,
                    message=f"Invalid MCP request: {e}",
                ).model_dump(),
                status_code=400,
            )

        # Extraire le nom du tool et les arguments
        if not mcp_request.params:
            return JSONResponse(
                content=MCPResponse.failure(
                    request_id=mcp_request.id,
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Missing params",
                ).model_dump(),
                status_code=400,
            )

        tool_name = mcp_request.params.get("name")
        tool_arguments = mcp_request.params.get("arguments", {})

        # Extraire la confidence si fournie (pour SAFEGUARD L1)
        confidence = mcp_request.params.get("confidence", 100.0)

        if not tool_name:
            return JSONResponse(
                content=MCPResponse.failure(
                    request_id=mcp_request.id,
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Missing tool name in params",
                ).model_dump(),
                status_code=400,
            )

        # =================================================================
        # SAFEGUARD: Vérifier le niveau de sécurité AVANT exécution
        # =================================================================
        safeguard_result = check_safeguard(tool_name, confidence)

        if not safeguard_result.allowed:
            logger.warning(
                "safeguard_blocked",
                tool_name=tool_name,
                level=safeguard_result.level.value,
                message=safeguard_result.message,
                approval_id=safeguard_result.pending_approval_id,
            )
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.id,
                    "error": {
                        "code": -32001,  # Custom error code for SAFEGUARD
                        "message": safeguard_result.message,
                        "data": safeguard_result.to_dict(),
                    },
                },
                status_code=403,
            )

        # Créer le contexte d'exécution
        context = ExecutionContext(
            request_id=str(mcp_request.id),
            tool_name=tool_name,
            caller=request.client.host if request.client else None,
        )

        # Exécuter le tool
        response = await tool_registry.execute(
            tool_name=tool_name,
            arguments=tool_arguments,
            context=context,
        )

        # Log de l'exécution
        logger.info(
            "mcp_call_completed",
            tool_name=tool_name,
            request_id=mcp_request.id,
            success=response.error is None,
            elapsed_ms=context.elapsed_ms,
            security_level=safeguard_result.level.value,
        )

        return JSONResponse(content=response.model_dump())

    # -------------------------------------------------------------------------
    # Liste des tools avec niveaux de sécurité
    # -------------------------------------------------------------------------

    @app.get("/mcp/tools")
    async def list_tools(
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> dict[str, Any]:
        """Liste tous les tools disponibles avec leurs niveaux SAFEGUARD."""
        tools = tool_registry.get_schemas()

        # Enrichir avec les niveaux de sécurité
        enriched_tools = []
        for tool in tools:
            tool_name = tool.get("name", "")
            level = TOOL_SECURITY_LEVELS.get(tool_name, SecurityLevel.L0_READ_ONLY)
            enriched_tools.append({
                **tool,
                "security_level": level.value,
                "security_description": {
                    "L0": "Lecture seule - Auto",
                    "L1": "Action mineure - Auto si confidence >= 80%",
                    "L2": "Action modérée - Avec notification",
                    "L3": "Action sensible - Validation humaine requise",
                    "L4": "Interdit à l'IA - Humain uniquement",
                }.get(level.value, "Inconnu"),
            })

        return {
            "count": len(enriched_tools),
            "safeguard_enabled": settings.safeguard_enabled,
            "tools": enriched_tools,
        }

    # -------------------------------------------------------------------------
    # Exécution directe (alternative sans JSON-RPC)
    # -------------------------------------------------------------------------

    @app.post("/tools/{tool_name}")
    async def execute_tool_direct(
        tool_name: str,
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Exécution directe d'un tool (sans enveloppe JSON-RPC).

        SAFEGUARD: Vérifie les niveaux de sécurité avant exécution.
        """
        try:
            arguments = await request.json()
        except Exception:
            arguments = {}

        # Extraire confidence si fournie
        confidence = arguments.pop("_confidence", 100.0)

        # SAFEGUARD check
        safeguard_result = check_safeguard(tool_name, confidence)

        if not safeguard_result.allowed:
            return JSONResponse(
                content={
                    "error": "SAFEGUARD_BLOCKED",
                    "details": safeguard_result.to_dict(),
                },
                status_code=403,
            )

        context = ExecutionContext(
            request_id=f"direct-{datetime.utcnow().timestamp()}",
            tool_name=tool_name,
            caller=request.client.host if request.client else None,
        )

        response = await tool_registry.execute(
            tool_name=tool_name,
            arguments=arguments,
            context=context,
        )

        if response.error:
            return JSONResponse(
                content={"error": response.error.model_dump()},
                status_code=400 if response.error.code > -32700 else 500,
            )

        return JSONResponse(content={
            "result": response.result,
            "security_level": safeguard_result.level.value,
        })

    # -------------------------------------------------------------------------
    # Endpoints SAFEGUARD - Queue d'approbation L3
    # -------------------------------------------------------------------------

    @app.post("/safeguard/request")
    async def create_approval_request(
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Crée une demande d'approbation pour une action L3.

        Body:
        {
            "tool_name": "ad_reset_password",
            "arguments": {"username": "jdoe"},
            "context": {"ticket_id": "12345", "reason": "User request"}
        }
        """
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                content={"error": "Invalid JSON body"},
                status_code=400,
            )

        tool_name = body.get("tool_name")
        arguments = body.get("arguments", {})
        context = body.get("context", {})
        ttl_minutes = body.get("ttl_minutes", 60)

        if not tool_name:
            return JSONResponse(
                content={"error": "tool_name is required"},
                status_code=400,
            )

        # Vérifier que c'est bien un tool L3
        level = TOOL_SECURITY_LEVELS.get(tool_name)
        if level != SecurityLevel.L3_SENSITIVE:
            return JSONResponse(
                content={
                    "error": f"Tool '{tool_name}' is not L3. "
                             f"Level: {level.value if level else 'unknown'}. "
                             f"Only L3 tools require approval requests."
                },
                status_code=400,
            )

        # Créer la demande
        result = await safeguard_queue.create_approval_request(
            tool_name=tool_name,
            arguments=arguments,
            security_level=level.value,
            requester_ip=request.client.host if request.client else None,
            context=context,
            ttl_minutes=ttl_minutes,
        )

        return JSONResponse(content=result, status_code=201)

    @app.get("/safeguard/pending")
    async def list_pending_approvals(
        _api_key: Optional[str] = Depends(verify_api_key),
        limit: int = 50,
    ) -> dict[str, Any]:
        """Liste les demandes d'approbation en attente."""
        approvals = await safeguard_queue.get_pending_approvals(limit=limit)
        return {
            "count": len(approvals),
            "approvals": approvals,
        }

    @app.get("/safeguard/status/{approval_id}")
    async def get_approval_status(
        approval_id: str,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """Récupère le statut d'une demande d'approbation."""
        status = await safeguard_queue.get_approval_status(approval_id)

        if not status:
            return JSONResponse(
                content={"error": "Approval request not found"},
                status_code=404,
            )

        return JSONResponse(content=status)

    @app.post("/safeguard/approve/{approval_id}")
    async def approve_action(
        approval_id: str,
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Approuve une action L3 en attente.

        Body:
        {
            "approver": "admin@widip.fr",
            "comment": "Approved after verification" (optional)
        }
        """
        try:
            body = await request.json()
        except Exception:
            body = {}

        approver = body.get("approver", "unknown")
        comment = body.get("comment")

        result = await safeguard_queue.approve(
            approval_id=approval_id,
            approver=approver,
            comment=comment,
        )

        status_code = 200 if result.get("success") else 400
        return JSONResponse(content=result, status_code=status_code)

    @app.post("/safeguard/reject/{approval_id}")
    async def reject_action(
        approval_id: str,
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Rejette une action L3 en attente.

        Body:
        {
            "approver": "admin@widip.fr",
            "comment": "Rejected - suspicious request" (optional)
        }
        """
        try:
            body = await request.json()
        except Exception:
            body = {}

        approver = body.get("approver", "unknown")
        comment = body.get("comment")

        result = await safeguard_queue.reject(
            approval_id=approval_id,
            approver=approver,
            comment=comment,
        )

        status_code = 200 if result.get("success") else 400
        return JSONResponse(content=result, status_code=status_code)

    @app.post("/safeguard/execute/{approval_id}")
    async def execute_approved_action(
        approval_id: str,
        request: Request,
        _api_key: Optional[str] = Depends(verify_api_key),
    ) -> JSONResponse:
        """
        Exécute une action L3 préalablement approuvée.

        Cette endpoint permet d'exécuter le tool après approbation humaine.
        """
        # Récupérer la demande
        approval = await safeguard_queue.get_approval_status(approval_id)

        if not approval:
            return JSONResponse(
                content={"error": "Approval request not found"},
                status_code=404,
            )

        if approval["status"] != ApprovalStatus.APPROVED.value:
            return JSONResponse(
                content={
                    "error": f"Cannot execute: status is '{approval['status']}', "
                             f"expected 'approved'"
                },
                status_code=400,
            )

        # Exécuter le tool
        tool_name = approval["tool_name"]
        arguments = approval["arguments"]

        context = ExecutionContext(
            request_id=f"approved-{approval_id}",
            tool_name=tool_name,
            caller=request.client.host if request.client else None,
        )

        try:
            response = await tool_registry.execute(
                tool_name=tool_name,
                arguments=arguments,
                context=context,
            )

            if response.error:
                await safeguard_queue.mark_executed(
                    approval_id=approval_id,
                    error=str(response.error),
                )
                return JSONResponse(
                    content={
                        "success": False,
                        "approval_id": approval_id,
                        "error": response.error.model_dump(),
                    },
                    status_code=500,
                )

            await safeguard_queue.mark_executed(
                approval_id=approval_id,
                result=response.result,
            )

            logger.info(
                "safeguard_l3_executed",
                approval_id=approval_id,
                tool_name=tool_name,
            )

            return JSONResponse(content={
                "success": True,
                "approval_id": approval_id,
                "tool_name": tool_name,
                "result": response.result,
            })

        except Exception as e:
            await safeguard_queue.mark_executed(
                approval_id=approval_id,
                error=str(e),
            )
            return JSONResponse(
                content={
                    "success": False,
                    "approval_id": approval_id,
                    "error": str(e),
                },
                status_code=500,
            )
