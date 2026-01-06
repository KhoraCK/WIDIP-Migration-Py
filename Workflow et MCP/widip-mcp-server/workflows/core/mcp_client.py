"""
MCP Client - HTTP client to call MCP Server tools
"""

import asyncio
from typing import Any, Optional
from uuid import uuid4

import httpx
import structlog

from .exceptions import MCPError, SafeguardBlockedError

logger = structlog.get_logger()


class MCPClient:
    """
    Async HTTP client to call MCP Server tools.

    The MCP Server runs on port 3001 and exposes tools via JSON-RPC 2.0.
    This client handles:
    - Tool calls via /mcp/call endpoint
    - SAFEGUARD blocked responses
    - Retries with exponential backoff
    - Timeout handling
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        api_key: str = None,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize MCP Client.

        Args:
            base_url: MCP Server URL (default: http://localhost:3001)
            api_key: API key for authentication (X-API-Key header)
            timeout_seconds: Request timeout
            max_retries: Number of retries on transient errors
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.timeout_seconds),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def call(
        self,
        tool_name: str,
        arguments: dict = None,
        confidence: float = None,
    ) -> Any:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            confidence: Optional confidence score (for SAFEGUARD)

        Returns:
            Tool result

        Raises:
            MCPError: If tool call fails
            SafeguardBlockedError: If action blocked by SAFEGUARD
        """
        client = await self._get_client()

        # Build JSON-RPC request
        request_id = str(uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": tool_name,
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }

        # Add confidence if provided
        if confidence is not None:
            payload["params"]["confidence"] = confidence

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "mcp_call_attempt",
                    tool=tool_name,
                    attempt=attempt,
                    max_retries=self.max_retries,
                )

                response = await client.post("/mcp/call", json=payload)

                # Handle HTTP errors
                if response.status_code == 403:
                    raise MCPError(
                        "Authentication failed",
                        tool_name=tool_name,
                        error_code=403,
                    )

                if response.status_code == 404:
                    raise MCPError(
                        f"Tool not found: {tool_name}",
                        tool_name=tool_name,
                        error_code=404,
                    )

                if response.status_code >= 500:
                    # Server error - retry
                    raise MCPError(
                        f"MCP Server error: {response.status_code}",
                        tool_name=tool_name,
                        error_code=response.status_code,
                    )

                response.raise_for_status()

                # Parse JSON-RPC response
                data = response.json()

                # Check for JSON-RPC error
                if "error" in data:
                    error = data["error"]
                    error_message = error.get("message", "Unknown error")
                    error_code = error.get("code", -1)
                    error_data = error.get("data", {})

                    # Check if SAFEGUARD blocked
                    if error_code == -32003 or "safeguard" in error_message.lower():
                        approval_id = error_data.get("approval_id")
                        raise SafeguardBlockedError(
                            message=error_message,
                            tool_name=tool_name,
                            security_level=error_data.get("security_level"),
                            approval_id=approval_id,
                        )

                    raise MCPError(
                        error_message,
                        tool_name=tool_name,
                        error_code=error_code,
                        mcp_response=error_data,
                    )

                # Success
                result = data.get("result")

                logger.debug(
                    "mcp_call_success",
                    tool=tool_name,
                    attempt=attempt,
                )

                return result

            except SafeguardBlockedError:
                # Don't retry SAFEGUARD blocks
                raise

            except MCPError as e:
                if e.error_code in (403, 404):
                    # Don't retry auth or not found errors
                    raise
                last_error = e

            except httpx.TimeoutException as e:
                last_error = MCPError(
                    f"Timeout calling {tool_name}",
                    tool_name=tool_name,
                    error_code=-1,
                )

            except httpx.RequestError as e:
                last_error = MCPError(
                    f"Connection error: {str(e)}",
                    tool_name=tool_name,
                    error_code=-1,
                )

            except Exception as e:
                last_error = MCPError(
                    f"Unexpected error: {str(e)}",
                    tool_name=tool_name,
                    error_code=-1,
                )

            # Exponential backoff before retry
            if attempt < self.max_retries:
                wait_time = min(2 ** attempt, 10)  # Max 10 seconds
                logger.warning(
                    "mcp_call_retry",
                    tool=tool_name,
                    attempt=attempt,
                    wait_seconds=wait_time,
                    error=str(last_error),
                )
                await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            "mcp_call_failed",
            tool=tool_name,
            attempts=self.max_retries,
            error=str(last_error),
        )
        raise last_error

    async def health_check(self) -> dict:
        """
        Check MCP Server health.

        Returns:
            Health status dict
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def list_tools(self) -> list:
        """
        List available MCP tools.

        Returns:
            List of tool definitions
        """
        try:
            client = await self._get_client()
            response = await client.get("/mcp/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("mcp_list_tools_failed", error=str(e))
            return []

    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
