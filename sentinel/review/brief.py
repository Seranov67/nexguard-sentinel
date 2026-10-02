"""Human-readable evidence brief, with exact amounts and explicit provenance."""

import json
from typing import Any


def json_brief(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def text_brief(value: dict[str, Any]) -> str:
    case = value["case"]
    finding = case["finding"]
    observation = case["observation"]
    health = value["source_health"]
    gap = health.get("gap") or (
        "Source check is stale; refresh provider verification."
        if health["status"] == "stale"
        else "No additional source gap recorded."
    )
    lines = [
        "NexGuard Sentinel — Incident Review Brief",
        value["schema_version"],
        "SYNTHETIC FIXTURE" if value["synthetic"] else "LIVE PROVIDER OBSERVATION",
        f"Case: {case['id']}",
        f"Review status: {case['status']} (revision {case['revision']})",
        f"Disposition: {case['disposition'] or 'not yet recorded'}",
        f"Source integrity: {value['finding_integrity']}",
        f"Source status: {health['status']} (recorded: {health['recorded_status']})",
        f"Source checked at: {health.get('checked_at') or 'not recorded'}",
        f"Source gap: {gap}",
        f"Policy: {finding['policy_version']} / {finding['rule']}",
        f"Amount: {finding['observed_amount']} {finding['unit']}",
        f"Threshold: {finding['threshold']} ({finding['comparison']})",
        f"Source entity: {observation['id']}",
        f"Observed at: {observation['observed_at']}",
        f"Payload SHA-256: {observation['payload_sha256']}",
        f"Legacy action evidence: {value['legacy_action']['status']}",
        "",
        "Operator history:",
    ]
    for action in case["history"]:
        lines += [
            f"{action['at']} — {action['operator']} — {action['status']}",
            f"Disposition: {action['disposition'] or 'pending'}",
            action["note"],
        ]
    lines += ["", "Links:"] + [f"{key}: {url}" for key, url in value["links"].items()]
    lines += ["", "Limits:"] + value["limits"]
    # The JSON section retains original fields, proofs, actual outcomes and all gaps.
    lines += ["", "Full evidence:", json_brief(value)]
    return "\n".join(lines) + "\n"
