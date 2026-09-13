"""Cliente MCP minimalista para `arggon mcp` (JSON-RPC sobre stdio).

Uso desde Python::

    from tools.mcp_client import ArggonMCP

    with ArggonMCP() as mcp:
        mcp.call("arggon_list", {"status": "todo"})
        mcp.call("arggon_comment", {"id": "status-report", "body": "hola"})

Protocolo: una línea JSON por mensaje en stdin/stdout (newline-delimited JSON).
El `initialize` (protocolVersion "2024-11-05") va primero, luego la notificación
`notifications/initialized`, y recién entonces `tools/list` / `tools/call`.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

PROTOCOL_VERSION = "2024-11-05"


class MCPError(RuntimeError):
    """Fallo de transporte o error devuelto por el servidor MCP."""


class ArggonMCP:
    """Sesión con el servidor MCP de arggon (spawn de `arggon mcp`)."""

    def __init__(self, log: list[dict[str, Any]] | None = None) -> None:
        self._next_id = 0
        self.log = log if log is not None else []
        self.server_info: dict[str, Any] = {}
        self._proc = subprocess.Popen(
            ["arggon", "mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _send(self, message: dict[str, Any]) -> None:
        assert self._proc.stdin is not None
        line = json.dumps(message)
        self.log.append({"direction": ">>", "message": message})
        self._proc.stdin.write(line + "\n")
        self._proc.stdin.flush()

    def _recv(self) -> dict[str, Any]:
        assert self._proc.stdout is not None
        line = self._proc.stdout.readline()
        if not line:
            stderr = self._proc.stderr.read() if self._proc.stderr else ""
            raise MCPError(f"el servidor cerró stdout. stderr: {stderr.strip()}")
        message = json.loads(line)
        self.log.append({"direction": "<<", "message": message})
        return message

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Request JSON-RPC con id; devuelve `result` o lanza MCPError."""
        self._next_id += 1
        request: dict[str, Any] = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            request["params"] = params
        self._send(request)
        while True:
            response = self._recv()
            if response.get("id") == self._next_id:
                if "error" in response:
                    raise MCPError(f"{method}: {response['error']}")
                return response.get("result", {})

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "guardian-mcp-client", "version": "0.1.0"},
            },
        )
        self.server_info = result
        self.notify("notifications/initialized")
        return result

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """`tools/call`: devuelve el texto parseado del primer content block."""
        result = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        if result.get("isError"):
            raise MCPError(f"{name}: {result.get('content')}")
        for block in result.get("content", []):
            if block.get("type") == "text":
                text = block["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result

    def tools(self) -> list[dict[str, Any]]:
        return self.request("tools/list").get("tools", [])

    def __enter__(self) -> ArggonMCP:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        if self._proc.poll() is None:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.wait(timeout=10)
