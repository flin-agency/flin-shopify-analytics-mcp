"""Minimal JSON-RPC/MCP server implementation."""

from __future__ import annotations

from typing import Any

from .config import Config, load_config
from .shopify_client import ShopifyClient
from .tools import TOOL_DEFINITIONS, call_tool


JSONRPC_VERSION = "2.0"
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "flin-shopify-analytics-mcp", "version": "0.2.1"}


class ShopifyAnalyticsMcpServer:
    def __init__(self, client: ShopifyClient | None = None, config: Config | None = None):
        if client is not None:
            self.client = client
        else:
            resolved_config = config or load_config()
            self.client = ShopifyClient(resolved_config)
        self.initialized = False

    @staticmethod
    def _is_notification(message: dict[str, Any]) -> bool:
        return "id" not in message

    @staticmethod
    def _error(code: int, message: str, data: Any | None = None) -> dict[str, Any]:
        payload = {"code": code, "message": message}
        if data is not None:
            payload["data"] = data
        return payload

    def handle_message(self, message: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return {"jsonrpc": JSONRPC_VERSION, "id": None, "error": self._error(-32600, "Invalid Request")}

        method = message.get("method")
        if not isinstance(method, str):
            if self._is_notification(message):
                return None
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": message.get("id"),
                "error": self._error(-32600, "Invalid Request"),
            }

        try:
            result = self._dispatch(method, message.get("params") or {})
            if self._is_notification(message):
                return None
            return {"jsonrpc": JSONRPC_VERSION, "id": message["id"], "result": result}
        except Exception as exc:  # pragma: no cover
            if self._is_notification(message):
                return None
            code = getattr(exc, "code", -32000)
            text = str(exc)
            return {"jsonrpc": JSONRPC_VERSION, "id": message.get("id"), "error": self._error(code, text)}

    def _assert_initialized(self, method: str) -> None:
        if not self.initialized:
            error = RuntimeError(f"Server not initialized. Call initialize before {method}.")
            setattr(error, "code", -32002)
            raise error

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            self.initialized = True
            return {
                "protocolVersion": params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            }
        if method == "notifications/initialized":
            return {}
        if method == "ping":
            return {}
        if method == "tools/list":
            self._assert_initialized(method)
            return {"tools": TOOL_DEFINITIONS}
        if method == "tools/call":
            self._assert_initialized(method)
            return self._handle_tool_call(params)
        if method == "resources/list":
            self._assert_initialized(method)
            return {"resources": []}
        if method == "prompts/list":
            self._assert_initialized(method)
            return {"prompts": []}

        error = RuntimeError(f"Method not found: {method}")
        setattr(error, "code", -32601)
        raise error

    def _handle_tool_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            error = RuntimeError("Invalid params: tools/call requires a string `name`.")
            setattr(error, "code", -32602)
            raise error

        try:
            return call_tool(self.client, name, params.get("arguments") or {})
        except Exception as exc:
            return {"content": [{"type": "text", "text": f"Tool failed: {exc}"}], "isError": True}
