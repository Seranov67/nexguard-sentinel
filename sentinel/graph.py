"""Bounded live Graph ingestion with confirmation checks and restart replay."""

from collections.abc import Callable
from typing import Any

import httpx

from sentinel.config import Settings
from sentinel.models import Withdrawal, hex_value
from sentinel.store import StateStore

QUERY = """
query Withdrawals($after: BigInt!, $through: BigInt!, $snapshot: Int!) {
 withdrawals(first: 100, orderBy: sequence, orderDirection: asc,
   block: {number: $snapshot},
   where: {sequence_gt: $after, blockNumber_lte: $through}) {
   id sequence blockNumber blockHash transactionHash logIndex timestamp who amount
 }
 _meta(block: {number: $snapshot}) { block {number hash} hasIndexingErrors }
}
"""
META = "{ _meta { block { number hash } hasIndexingErrors } }"


class GraphSource:
    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        block_hash: Callable[[int], str],
        client: httpx.Client,
    ) -> None:
        self.settings = settings
        self.store = store
        self.block_hash = block_hash
        self.client = client
        self.source = f"84532:{settings.vault_address.lower()}"

    def query(self, query: str, variables: dict[str, str | int]) -> dict[str, Any]:
        response = self.client.post(
            self.settings.subgraph_url, json={"query": query, "variables": variables}, timeout=20
        )
        response.raise_for_status()
        if len(response.content) > 1_000_000:
            raise ValueError("Graph response too large")
        raw = response.json()
        if not isinstance(raw, dict) or raw.get("errors") or not isinstance(raw.get("data"), dict):
            raise ValueError("Invalid Graph response")
        data: dict[str, Any] = raw["data"]
        meta = data["_meta"]
        if meta.get("hasIndexingErrors") is not False:
            raise ValueError("Graph indexing errors or missing health evidence")
        height = int(meta["block"]["number"])
        if height < 0 or hex_value(meta["block"]["hash"], 32) != self.block_hash(height).lower():
            raise ValueError("Graph/RPC block disagreement")
        return data

    def poll(self, rpc_head: int) -> int:
        """Commit ingestion, then let the runtime drain durable unhandled events.

        A fixed Graph snapshot prevents paging over changing indexes. Every poll
        rewinds, including the first poll after a restart; dedupe is durable.
        """
        try:
            meta = self.query(META, {})["_meta"]
            snapshot = int(meta["block"]["number"])
            through = min(snapshot, rpc_head) - self.settings.confirmations + 1
            cursor = self.store.cursor(self.source)
            if cursor is not None and through < cursor[1]:
                raise ValueError("Confirmed Graph head regressed")
            after = (
                -1
                if cursor is None
                else (max(0, cursor[1] - self.settings.rewind_blocks) * 1_000_000 - 1)
            )
            added = 0
            if through < 0:
                return added
            for _ in range(100):
                data = self.query(
                    QUERY, {"after": str(after), "through": str(through), "snapshot": snapshot}
                )
                if int(data["_meta"]["block"]["number"]) != snapshot:
                    raise ValueError("Graph snapshot changed")
                rows = data["withdrawals"]
                if not isinstance(rows, list) or len(rows) > 100:
                    raise ValueError("Invalid Graph page")
                events = [Withdrawal.parse(row) for row in rows]
                previous = after
                for event in events:
                    if event.sequence <= previous or event.block > through:
                        raise ValueError("Unordered or unconfirmed Graph event")
                    if event.block_hash != self.block_hash(event.block).lower():
                        raise ValueError("Graph event is not canonical")
                    previous = event.sequence
                for event in events:
                    added += self.store.ingest(
                        self.source, event.id, event.sequence, event.block, event.payload()
                    )
                if len(events) < 100:
                    return added
                after = events[-1].sequence
            return added  # Bounded work; the durable cursor continues on the next poll.
        except Exception:
            self.store.set_latch("Graph ingestion failed; verify source and RPC before reset")
            raise
