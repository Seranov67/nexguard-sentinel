"""Bazantic MCP Server for NexGuard Sentinel Incident Investigation.

Implements the Model Context Protocol (MCP) tool interface so that an AI agent
connected to a Bazantic gateway can:

  1. Retrieve the latest critical incident with cryptographic evidence.
  2. Verify a specific incident's evidence against the local SQLite audit trail.

The server communicates over stdio (standard MCP transport) and requires the
Sentinel Evidence API to be reachable at EVIDENCE_API_URL (default: localhost).

Usage:
    python -m sentinel.bazantic.mcp_server

Or from an MCP-compatible host via the installed recipe.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EVIDENCE_API_URL = os.environ.get("EVIDENCE_API_URL", "http://localhost:8080")
_HEADERS = {"X-Dev-Mode": "1", "Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# MCP message helpers (stdio transport, JSON-RPC 2.0)
# ---------------------------------------------------------------------------


def _send(obj: dict[str, Any]) -> None:
    """Write a JSON-RPC response to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error(req_id: str | int | None, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _result(req_id: str | int | None, content: list[dict[str, Any]]) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": {"content": content}})


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _get_latest_incident() -> dict[str, Any]:
    """Call the Evidence API and return the structured incident record."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{EVIDENCE_API_URL}/api/v1/incidents/latest", headers=_HEADERS)
    if resp.status_code == 404:
        return {
            "found": False,
            "message": "No incidents recorded yet. "
            "The Sentinel event loop must observe at least one critical event.",
        }
    resp.raise_for_status()
    data = resp.json()
    return {
        "found": True,
        "incident_id": data["incident_id"],
        "created_at": data["created_at"],
        "status": data["status"],
        "trigger_cause": data["trigger_cause"],
        "pause_evidence": data["pause_evidence"],
        "guardian_address": data["guardian"]["address"],
        "vault_address": data["vault"]["address"],
        "chain_id": data["chain_id"],
        "sha256_fingerprint": data["sha256_state_fingerprint"],
        "agent_summary": data["agent_summary"],
        "source_event_count": len(data.get("source_event_ids", [])),
    }


def _verify_incident_evidence(incident_id: str) -> dict[str, Any]:
    """Verify a specific incident and cross-reference its evidence fields."""
    if not incident_id or len(incident_id) > 128:
        return {"verified": False, "error": "invalid_incident_id"}
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{EVIDENCE_API_URL}/api/v1/incidents/{incident_id}",
            headers=_HEADERS,
        )
    if resp.status_code == 404:
        return {"verified": False, "error": "incident_not_found", "incident_id": incident_id}
    resp.raise_for_status()
    data = resp.json()

    # Cross-reference evidence consistency
    issues: list[str] = []
    if not data.get("sha256_state_fingerprint"):
        issues.append("missing SHA-256 fingerprint")
    pause_ev = data.get("pause_evidence", {})
    if data["status"] == "success" and not pause_ev.get("tx_hash"):
        issues.append("status=success but no tx_hash in pause evidence")
    if data["chain_id"] != 84532:
        issues.append(f"unexpected chain_id: {data['chain_id']}")

    return {
        "verified": len(issues) == 0,
        "incident_id": data["incident_id"],
        "status": data["status"],
        "tx_hash": pause_ev.get("tx_hash"),
        "sha256_fingerprint": data.get("sha256_state_fingerprint"),
        "issues": issues,
        "agent_summary": data.get("agent_summary"),
    }


# ---------------------------------------------------------------------------
# MCP dispatch loop
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "get_latest_incident",
        "description": textwrap.dedent("""\
            Retrieve the latest critical NexGuard Sentinel incident with full
            cryptographic evidence: Guardian.pause() transaction hash on Base Sepolia,
            Basescan explorer URL, The Graph entity IDs, and a SHA-256 state fingerprint.
            Use this tool first to find the incident and understand why the Vault was paused.
        """).strip(),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "verify_incident_evidence",
        "description": textwrap.dedent("""\
            Verify and cross-reference all evidence fields for a specific incident ID.
            Checks that the SHA-256 fingerprint is present, the pause tx hash is recorded
            for successful incidents, and the chain ID matches Base Sepolia.
            Returns a verified flag and a list of any consistency issues found.
        """).strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "incident_id": {
                    "type": "string",
                    "description": "The incident UUID returned by get_latest_incident.",
                }
            },
            "required": ["incident_id"],
        },
    },
]


def _handle_initialize(req_id: str | int | None) -> None:
    _send({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "nexguard-sentinel-mcp",
                "version": "1.0.0",
            },
            "capabilities": {"tools": {}},
        },
    })


def _handle_tools_list(req_id: str | int | None) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOL_DEFINITIONS}})


def _handle_tools_call(req_id: str | int | None, params: dict[str, Any]) -> None:
    name = params.get("name", "")
    args = params.get("arguments", {})
    try:
        if name == "get_latest_incident":
            data = _get_latest_incident()
        elif name == "verify_incident_evidence":
            data = _verify_incident_evidence(str(args.get("incident_id", "")))
        else:
            _error(req_id, -32601, f"Unknown tool: {name}")
            return
        _result(req_id, [{"type": "text", "text": json.dumps(data, indent=2)}])
    except httpx.HTTPError as exc:
        _error(req_id, -32000, f"Evidence API unreachable: {exc}")
    except Exception as exc:
        _error(req_id, -32000, f"Tool error: {exc}")


def serve() -> None:
    """Run the MCP server; read JSON-RPC messages from stdin line by line."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            _error(None, -32700, "Parse error")
            continue
        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})
        if method == "initialize":
            _handle_initialize(req_id)
        elif method == "tools/list":
            _handle_tools_list(req_id)
        elif method == "tools/call":
            _handle_tools_call(req_id, params)
        elif method == "notifications/initialized":
            pass  # no response needed
        else:
            if req_id is not None:
                _error(req_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    serve()
