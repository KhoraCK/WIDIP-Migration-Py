"""
Registre des tools MCP.

Ce module gère l'enregistrement et la découverte des tools disponibles.
"""

import asyncio
import inspect
from typing import Any, Callable, Optional

import structlog

from .protocol import (
    ExecutionContext,
    MCPErrorCode,
    MCPResponse,
    MCPTool,
    ToolHandler,
    ToolParameter,
    ToolParameterType,
)

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """
    Registre centralisé des tools MCP.

    Gère l'enregistrement, la découverte et l'exécution des tools.
    Singleton pattern pour un accès global.
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """
        Enregistre un tool dans le registre.

        Args:
            tool: Tool MCP à enregistrer

        Raises:
            ValueError: Si un tool avec le même nom existe déjà
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")

        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name)

    def register_function(
        self,
        name: str,
        description: str,
        parameters: Optional[dict[str, ToolParameter]] = None,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """
        Décorateur pour enregistrer une fonction comme tool MCP.

        Usage:
            @tool_registry.register_function(
                name="create_ticket",
                description="Crée un ticket GLPI",
                parameters={...}
            )
            async def create_ticket(title: str, description: str) -> dict:
                ...

        Args:
            name: Nom du tool
            description: Description pour l'agent IA
            parameters: Définition des paramètres

        Returns:
            Décorateur
        """

        def decorator(func: ToolHandler) -> ToolHandler:
            tool = MCPTool(
                name=name,
                description=description,
                parameters=parameters or {},
                handler=func,
            )
            self.register(tool)
            return func

        return decorator

    def get(self, name: str) -> Optional[MCPTool]:
        """Récupère un tool par son nom."""
        return self._tools.get(name)

    def get_all(self) -> list[MCPTool]:
        """Retourne tous les tools enregistrés."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Retourne les schémas MCP de tous les tools."""
        return [tool.to_mcp_schema() for tool in self._tools.values()]

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> MCPResponse:
        """
        Exécute un tool avec les arguments fournis.

        Args:
            tool_name: Nom du tool à exécuter
            arguments: Arguments passés au tool
            context: Contexte d'exécution (optionnel)

        Returns:
            MCPResponse avec le résultat ou l'erreur
        """
        request_id = context.request_id if context else "unknown"

        # Vérifier que le tool existe
        tool = self.get(tool_name)
        if not tool:
            logger.warning("tool_not_found", tool_name=tool_name)
            return MCPResponse.failure(
                request_id=request_id,
                code=MCPErrorCode.TOOL_NOT_FOUND,
                message=f"Tool '{tool_name}' not found",
            )

        if not tool.handler:
            logger.error("tool_no_handler", tool_name=tool_name)
            return MCPResponse.failure(
                request_id=request_id,
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Tool '{tool_name}' has no handler",
            )

        # Exécuter le handler
        try:
            logger.info(
                "tool_execution_start",
                tool_name=tool_name,
                arguments=arguments,
            )

            # Support des handlers sync et async
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                # Exécuter les fonctions sync dans un thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool.handler(**arguments)  # type: ignore
                )

            elapsed_ms = context.elapsed_ms if context else 0
            logger.info(
                "tool_execution_success",
                tool_name=tool_name,
                elapsed_ms=elapsed_ms,
            )

            return MCPResponse.success(request_id=request_id, result=result)

        except TypeError as e:
            # Erreur de paramètres (arguments manquants ou invalides)
            logger.warning(
                "tool_invalid_params",
                tool_name=tool_name,
                error=str(e),
            )
            return MCPResponse.failure(
                request_id=request_id,
                code=MCPErrorCode.INVALID_PARAMS,
                message=f"Invalid parameters: {e}",
            )

        except Exception as e:
            # Erreur d'exécution
            logger.exception(
                "tool_execution_error",
                tool_name=tool_name,
                error=str(e),
            )
            return MCPResponse.failure(
                request_id=request_id,
                code=MCPErrorCode.TOOL_EXECUTION_ERROR,
                message=f"Tool execution failed: {e}",
                data={"error_type": type(e).__name__},
            )

    def __contains__(self, name: str) -> bool:
        """Vérifie si un tool existe."""
        return name in self._tools

    def __len__(self) -> int:
        """Nombre de tools enregistrés."""
        return len(self._tools)


# Instance singleton du registre
tool_registry = ToolRegistry()


# =============================================================================
# Helpers pour créer des paramètres rapidement
# =============================================================================


def string_param(
    description: str,
    required: bool = False,
    default: Optional[str] = None,
    enum: Optional[list[str]] = None,
) -> ToolParameter:
    """Crée un paramètre de type string."""
    return ToolParameter(
        type=ToolParameterType.STRING,
        description=description,
        required=required,
        default=default,
        enum=enum,
    )


def int_param(
    description: str,
    required: bool = False,
    default: Optional[int] = None,
) -> ToolParameter:
    """Crée un paramètre de type integer."""
    return ToolParameter(
        type=ToolParameterType.INTEGER,
        description=description,
        required=required,
        default=default,
    )


def bool_param(
    description: str,
    required: bool = False,
    default: Optional[bool] = None,
) -> ToolParameter:
    """Crée un paramètre de type boolean."""
    return ToolParameter(
        type=ToolParameterType.BOOLEAN,
        description=description,
        required=required,
        default=default,
    )


def array_param(
    description: str,
    items_type: ToolParameterType = ToolParameterType.STRING,
    required: bool = False,
) -> ToolParameter:
    """Crée un paramètre de type array."""
    return ToolParameter(
        type=ToolParameterType.ARRAY,
        description=description,
        required=required,
        items={"type": items_type.value},
    )
