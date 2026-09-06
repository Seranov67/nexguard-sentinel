"""Versioned canonical bytes shared by policy, signer and evidence consumers."""

import hashlib
import json


def incident_proof(chain_id: int, guardian: str, event_ids: list[str]) -> tuple[str, str]:
    payload = json.dumps(
        {
            "version": 1,
            "chain_id": chain_id,
            "guardian": guardian.lower(),
            "action": "pause",
            "event_ids": sorted(event_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return payload, "0x" + hashlib.sha256(payload.encode("ascii")).hexdigest()
