"""Validated Graph entities and versioned, deterministic incident references."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from web3 import Web3


def hex_value(value: object, size: int) -> str:
    if not isinstance(value, str) or len(value) != 2 + size * 2 or not value.startswith("0x"):
        raise ValueError("Invalid hexadecimal identity")
    bytes.fromhex(value[2:])
    return value.lower()


@dataclass(frozen=True)
class Withdrawal:
    id: str
    sequence: int
    block: int
    block_hash: str
    tx_hash: str
    log_index: int
    timestamp: int
    actor: str
    amount: int

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> "Withdrawal":
        def number(key: str) -> int:
            value = raw[key]
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise ValueError("Expected a nonnegative decimal integer")
            if not str(value).isascii() or not str(value).isdecimal():
                raise ValueError("Expected a nonnegative decimal integer")
            return int(value)

        tx = hex_value(raw["transactionHash"], 32)
        index = number("logIndex")
        block = number("blockNumber")
        sequence = number("sequence")
        identity = hex_value(raw["id"], 36)
        if index >= 1_000_000 or sequence != block * 1_000_000 + index:
            raise ValueError("Invalid Graph event position")
        if identity != tx + index.to_bytes(4, "little").hex():
            raise ValueError("Noncanonical Graph event ID")
        return cls(
            identity,
            sequence,
            block,
            hex_value(raw["blockHash"], 32),
            tx,
            index,
            number("timestamp"),
            hex_value(raw["who"], 20),
            number("amount"),
        )

    def payload(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Proposal:
    """Validated classifier boundary; ES401 supplies these proposals."""

    severity: str
    action: str
    confidence: float
    rationale: str

    def permits_pause(self) -> bool:
        return (
            self.severity == "critical"
            and self.action == "pause"
            and 0.8 <= self.confidence <= 1.0
            and 0 < len(self.rationale) <= 240
        )


def canonical_incident(events: list[Withdrawal], guardian: str) -> bytes:
    if not events or len({event.id for event in events}) != len(events):
        raise ValueError("Unique source events are required")
    ordered = sorted(events, key=lambda event: event.sequence)
    payload = {
        "chain_id": "84532",
        "guardian": hex_value(guardian, 20),
        "schema_version": 1,
        "severity": "critical",
        "source_ids": [event.id for event in ordered],
        "timestamp": datetime.fromtimestamp(max(e.timestamp for e in events), UTC)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def incident_ref(payload: bytes) -> str:
    return "0x" + Web3.keccak(payload).hex()
