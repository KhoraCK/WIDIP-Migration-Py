"""
Implémentation du protocole MCP (Model Context Protocol).

Ce module définit les structures de données conformes au protocole MCP
pour une compatibilité maximale avec n8n 2.0 et les clients MCP standards.

Référence: https://modelcontextprotocol.io/
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Types de base
# =============================================================================


class ToolParameterType(str, Enum):
    """Types de paramètres supportés par les tools MCP."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """Définition d'un paramètre de tool MCP."""

    type: ToolParameterType = Field(description="Type du paramètre")
    description: str = Field(description="Description du paramètre")
    required: bool = Field(default=False, description="Paramètre obligatoire")
    default: Optional[Any] = Field(default=None, description="Valeur par défaut")
    enum: Optional[list[Any]] = Field(default=None, description="Valeurs possibles")
    items: Optional[dict[str, Any]] = Field(
        default=None, description="Schéma des éléments (pour array)"
    )
    properties: Optional[dict[str, Any]] = Field(
        default=None, description="Propriétés (pour object)"
    )


# =============================================================================
# Définition des Tools
# =============================================================================


# Type pour les handlers de tools (sync ou async)
ToolHandler = Callable[..., Union[Any, Coroutine[Any, Any, Any]]]


class MCPTool(BaseModel):
    """
    Définition d'un outil MCP.

    Un outil MCP expose une fonctionnalité aux agents IA via le protocole MCP.
    Il définit son nom, sa description, ses paramètres et sa fonction handler.
    """

    name: str = Field(description="Nom unique du tool (snake_case)")
    description: str = Field(description="Description pour l'agent IA")
    parameters: dict[str, ToolParameter] = Field(
        default_factory=dict, description="Paramètres du tool"
    )
    handler: Optional[ToolHandler] = Field(
        default=None, exclude=True, description="Fonction handler"
    )

    class Config:
        arbitrary_types_allowed = True

    def to_mcp_schema(self) -> dict[str, Any]:
        """
        Convertit le tool en schéma JSON compatible MCP.

        Format attendu par n8n MCP Client:
        {
            "name": "tool_name",
            "description": "Tool description",
            "inputSchema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        properties = {}
        required = []

        for param_name, param in self.parameters.items():
            prop: dict[str, Any] = {
                "type": param.type.value,
                "description": param.description,
            }

            if param.default is not None:
                prop["default"] = param.default
            if param.enum is not None:
                prop["enum"] = param.enum
            if param.items is not None:
                prop["items"] = param.items
            if param.properties is not None:
                prop["properties"] = param.properties

            properties[param_name] = prop

            if param.required:
                required.append(param_name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


# =============================================================================
# Messages JSON-RPC MCP
# =============================================================================


class MCPRequest(BaseModel):
    """
    Requête MCP au format JSON-RPC 2.0.

    Utilisé pour les appels de tools depuis n8n.
    """

    jsonrpc: str = Field(default="2.0", description="Version JSON-RPC")
    id: Union[str, int] = Field(description="ID de la requête")
    method: str = Field(description="Méthode appelée")
    params: Optional[dict[str, Any]] = Field(default=None, description="Paramètres")


class MCPError(BaseModel):
    """Erreur MCP au format JSON-RPC."""

    code: int = Field(description="Code d'erreur")
    message: str = Field(description="Message d'erreur")
    data: Optional[Any] = Field(default=None, description="Données additionnelles")


class MCPResponse(BaseModel):
    """
    Réponse MCP au format JSON-RPC 2.0.

    Retournée après l'exécution d'un tool.
    """

    jsonrpc: str = Field(default="2.0", description="Version JSON-RPC")
    id: Union[str, int] = Field(description="ID de la requête originale")
    result: Optional[Any] = Field(default=None, description="Résultat (si succès)")
    error: Optional[MCPError] = Field(default=None, description="Erreur (si échec)")

    @classmethod
    def success(cls, request_id: Union[str, int], result: Any) -> "MCPResponse":
        """Crée une réponse de succès."""
        return cls(id=request_id, result=result)

    @classmethod
    def failure(
        cls,
        request_id: Union[str, int],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> "MCPResponse":
        """Crée une réponse d'erreur."""
        return cls(id=request_id, error=MCPError(code=code, message=message, data=data))


# =============================================================================
# Codes d'erreur MCP (JSON-RPC standard + custom)
# =============================================================================


class MCPErrorCode:
    """Codes d'erreur MCP standards et custom."""

    # JSON-RPC standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom MCP errors (range -32000 to -32099)
    TOOL_NOT_FOUND = -32000
    TOOL_EXECUTION_ERROR = -32001
    AUTHENTICATION_ERROR = -32002
    RATE_LIMIT_ERROR = -32003
    EXTERNAL_API_ERROR = -32004
    VALIDATION_ERROR = -32005
    TIMEOUT_ERROR = -32006


# =============================================================================
# Messages SSE (Server-Sent Events)
# =============================================================================


class SSEMessage(BaseModel):
    """Message SSE pour le streaming MCP."""

    event: str = Field(description="Type d'événement")
    data: str = Field(description="Données JSON sérialisées")
    id: Optional[str] = Field(default=None, description="ID du message")
    retry: Optional[int] = Field(default=None, description="Délai de reconnexion (ms)")

    def format(self) -> str:
        """Formate le message pour envoi SSE."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        if self.retry:
            lines.append(f"retry: {self.retry}")
        lines.append(f"event: {self.event}")
        lines.append(f"data: {self.data}")
        lines.append("")  # Ligne vide pour terminer le message
        return "\n".join(lines)


# =============================================================================
# Contexte d'exécution
# =============================================================================


class ExecutionContext(BaseModel):
    """Contexte d'exécution d'un tool MCP."""

    request_id: str = Field(description="ID de la requête")
    tool_name: str = Field(description="Nom du tool appelé")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    caller: Optional[str] = Field(default=None, description="Identifiant de l'appelant")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def elapsed_ms(self) -> float:
        """Temps écoulé depuis le début de l'exécution."""
        return (datetime.utcnow() - self.started_at).total_seconds() * 1000
