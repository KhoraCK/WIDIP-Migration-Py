"""
Module MCP (Model Context Protocol)
====================================

Implémentation du protocole MCP pour n8n 2.0.
"""

from .protocol import MCPError, MCPRequest, MCPResponse, MCPTool, ToolParameter
from .registry import ToolRegistry, tool_registry
from .server import create_mcp_app

__all__ = [
    "MCPTool",
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "ToolParameter",
    "ToolRegistry",
    "tool_registry",
    "create_mcp_app",
]
