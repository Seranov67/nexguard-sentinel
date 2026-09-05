"""Validate a complete Graph page before persisting confirmed events.

Transport is injected so provider failures never become an empty successful page.
No signer or action authorization is exposed by this module.
"""

import json
import re
from collections.abc import Callable
from typing import Any

from sentinel.store import StateStore

QUERY = """query Withdrawals($after: BigInt!, $first: Int!, $block: Int!) {
  withdrawals(first: $first, orderBy: sequence, orderDirection: asc,
    block: {number: $block}, where: {sequence_gt: $after}) {
    id sequence blockNumber blockHash transactionHash logIndex timestamp
    who recipient triggeredBy amount remainingCredit
  }
  _meta(block: {number: $block}) { deployment hasIndexingErrors block {number hash} }
}"""


def natural(value: object) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ValueError("Expected an unsigned integer")
    return int(str(value))


def hex_value(value: object, size: int) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", value):
        raise ValueError("Malformed hexadecimal field")
    if len(value) != 2 + size * 2:
        raise ValueError("Incorrect hexadecimal field length")
    return value.lower()


class Ingestor:
    def __init__(
        self,
        store: StateStore,
        fetch: Callable[[str, dict[str, object]], dict[str, Any]],
        deployment: str,
        confirmations: int = 2,
        rewind_blocks: int = 2,
        page_size: int = 100,
    ) -> None:
        if confirmations < 1 or rewind_blocks < confirmations or not 1 <= page_size <= 1000:
            raise ValueError("Unsafe ingestion bounds")
        if not deployment:
            raise ValueError("Expected Graph deployment identity is required")
        self.store = store
        self.fetch = fetch
        self.deployment = deployment
        self.confirmations = confirmations
        self.rewind = rewind_blocks
        self.page_size = page_size

    def poll(self, chain_head: int, indexed_head: int, max_pages: int = 100) -> int:
        """Read a fixed confirmed snapshot; replay a block window on each poll.

        Head values must come from trusted chain/provider observations. Reorg
        conflicts raise through StateStore; the caller must latch before acting.
        """
        if max_pages < 1 or min(chain_head, indexed_head) < 0:
            raise ValueError("Invalid polling bounds")
        snapshot = min(chain_head, indexed_head) - self.confirmations
        if snapshot < 0:
            return 0
        cursor = self.store.cursor("vault-withdrawals")
        if cursor and snapshot < cursor[1]:
            raise ValueError("Provider is behind persisted state")
        after = -1 if cursor is None else max(0, cursor[1] - self.rewind) * 1_000_000 - 1
        inserted = 0
        for _ in range(max_pages):
            response = self.fetch(
                QUERY, {"after": str(after), "first": self.page_size, "block": snapshot}
            )
            if response.get("errors"):
                raise ValueError("Graph returned errors")
            data = response["data"]
            meta = data["_meta"]
            if meta["hasIndexingErrors"] is not False or meta["deployment"] != self.deployment:
                raise ValueError("Unexpected or unhealthy Graph deployment")
            if natural(meta["block"]["number"]) != snapshot:
                raise ValueError("Graph snapshot mismatch")
            hex_value(meta["block"]["hash"], 32)
            rows = data["withdrawals"]
            if not isinstance(rows, list) or len(rows) > self.page_size:
                raise ValueError("Invalid Graph page")
            validated: list[tuple[str, int, int, str]] = []
            for row in rows:
                sequence = natural(row["sequence"])
                block = natural(row["blockNumber"])
                log = natural(row["logIndex"])
                tx = hex_value(row["transactionHash"], 32)
                identity = hex_value(row["id"], 36)
                if log >= 1_000_000 or sequence != block * 1_000_000 + log:
                    raise ValueError("Invalid event sequence")
                if identity != tx + log.to_bytes(4, "little").hex():
                    raise ValueError("Invalid event identity")
                if sequence <= after or block > snapshot:
                    raise ValueError("Unordered or unconfirmed event")
                normalized = {
                    "id": identity,
                    "transactionHash": tx,
                    "blockHash": hex_value(row["blockHash"], 32),
                }
                for field in ("who", "recipient", "triggeredBy"):
                    normalized[field] = hex_value(row[field], 20)
                for field in (
                    "sequence",
                    "blockNumber",
                    "logIndex",
                    "timestamp",
                    "amount",
                    "remainingCredit",
                ):
                    normalized[field] = str(natural(row[field]))
                validated.append(
                    (
                        identity,
                        sequence,
                        block,
                        json.dumps(normalized, sort_keys=True, separators=(",", ":")),
                    )
                )
                after = sequence
            for identity, sequence, block, payload in validated:
                inserted += self.store.ingest(
                    "vault-withdrawals", identity, sequence, block, payload
                )
            if len(rows) < self.page_size:
                return inserted
        raise ValueError("Page budget exhausted; ingestion must catch up before action")
