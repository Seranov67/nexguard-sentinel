"""Real-model Recipe comparison. Missing services fail; no simulated scores are emitted."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from sentinel.bazantic.mcp_server import (
    TOOL_DEFINITIONS,
    _get_latest_incident,
    _verify_incident_evidence,
)

TASK_PROMPT = (
    "Find the latest critical incident in NexGuard Sentinel. Show its pause transaction "
    "hash and explorer link. Explain the recorded cause and verify evidence integrity. "
    "Do not infer missing AI or hardware evidence."
)


def run_agent(
    endpoint: str, model: str, recipe: str, timeout: float = 30
) -> dict[str, Any]:
    if not 0 < timeout <= 120:
        raise ValueError("Benchmark timeout must be within (0, 120] seconds")
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "Use available read-only tools to answer accurately. " + recipe,
        },
        {"role": "user", "content": TASK_PROMPT},
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"],
            },
        }
        for tool in TOOL_DEFINITIONS
    ]
    transcript: list[dict[str, Any]] = []
    for _ in range(6):
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                endpoint.rstrip("/") + "/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 512},
                },
            )
            response.raise_for_status()
        if len(response.content) > 65536:
            raise ValueError("Model response exceeds benchmark limit")
        data = response.json()
        if data.get("done") is not True:
            raise ValueError("Incomplete model response")
        message = data["message"]
        messages.append(message)
        calls = message.get("tool_calls", [])
        if not calls:
            return {"response": str(message.get("content", "")), "tool_calls": transcript}
        if len(calls) > 4:
            raise ValueError("Tool-call budget exceeded")
        for call in calls:
            function = call["function"]
            name = function["name"]
            arguments = function.get("arguments", {})
            if name == "get_latest_incident":
                result = _get_latest_incident()
            elif name == "verify_incident_evidence":
                result = _verify_incident_evidence(str(arguments.get("incident_id", "")))
            else:
                raise ValueError("Model requested a tool outside the read-only allowlist")
            transcript.append({"name": name, "arguments": arguments, "result": result})
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})
    raise ValueError("Agent did not finish within six rounds")


def score(result: dict[str, Any], evidence: dict[str, Any]) -> dict[str, bool]:
    response = str(result["response"])
    pause = evidence.get("pause_evidence", {})
    tx = pause.get("tx_hash")
    url = pause.get("explorer_url")
    verified = any(
        call["name"] == "verify_incident_evidence"
        and call["result"].get("verified") is True
        and call["result"].get("incident_id") == evidence["incident_id"]
        for call in result["tool_calls"]
    )
    return {
        "tx_hash_present": bool(tx and tx in response),
        "explorer_link_present": bool(url and url in response),
        "integrity_tool_succeeded": verified,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", ""))
    parser.add_argument(
        "--endpoint", default=os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("docs/ethonline/BAZANTIC_AB_BENCHMARK.md")
    )
    parser.add_argument("--timeout", type=float, default=30, help="Per-request seconds, max 120")
    args = parser.parse_args()
    if not 0 < args.timeout <= 120:
        parser.error("--timeout must be within (0, 120] seconds")
    if not args.model:
        parser.error("--model or OLLAMA_MODEL is required; simulated results are not supported")
    evidence = _get_latest_incident()
    if not evidence.get("found"):
        raise ValueError("A real persisted incident is required")
    recipe = Path(__file__).with_name("recipe.json").read_text(encoding="utf-8")
    results = {}
    for label, guidance in (("without_recipe", ""), ("with_recipe", recipe)):
        print(f"Running {label} with {args.model}", flush=True)
        result = run_agent(args.endpoint, args.model, guidance, args.timeout)
        result["structural_checks"] = score(result, evidence)
        result["reason_accuracy"] = "pending human review of transcript"
        results[label] = result
    if _get_latest_incident().get("incident_id") != evidence["incident_id"]:
        raise ValueError("Incident changed during comparison; rerun against a stable snapshot")
    report = {
        "run_at": datetime.now(UTC).isoformat(),
        "model": args.model,
        "temperature": 0,
        "timeout_seconds": args.timeout,
        "task": TASK_PROMPT,
        "incident_id": evidence["incident_id"],
        "simulated": False,
        "results": results,
    }
    text = (
        "# Bazantic real-model Recipe comparison\n\n"
        "Both runs use the same model, task, tools and settings. Only Recipe guidance differs.\n"
        "Structural checks are not a measure of explanation accuracy; human review is pending.\n\n"
        "```json\n" + json.dumps(report, indent=2) + "\n```\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=args.output.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = handle.name
    os.replace(temporary, args.output)
    print(f"Recorded real-model comparison: {args.output}")


if __name__ == "__main__":
    main()
