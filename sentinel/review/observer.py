"""Bounded Graph observer with a read-only RPC transport and no execution imports."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx
from web3 import Web3

from sentinel.models import Withdrawal, hex_value
from sentinel.review.models import CHAIN_ID, DEPLOYMENT, GUARDIAN, VAULT, utc_now
from sentinel.review.store import ReviewStore

META = "{ _meta { deployment block {number hash} hasIndexingErrors } }"
QUERY = """query Withdrawals($after: BigInt!, $through: BigInt!, $snapshot: Bytes!) {
 withdrawals(first:100, orderBy:sequence, orderDirection:asc, block:{hash:$snapshot},
 where:{sequence_gt:$after, blockNumber_lte:$through}) {
 id sequence blockNumber blockHash transactionHash logIndex timestamp
 who recipient triggeredBy amount remainingCredit
 }
 _meta(block:{hash:$snapshot}) { deployment block {number hash} hasIndexingErrors }
}"""


@dataclass(frozen=True)
class ObserveConfig:
    rpc_url: str = "https://sepolia.base.org"
    graph_url: str = "https://api.studio.thegraph.com/query/1758726/nexguard-sentinel/v0.1.0"
    confirmations: int = 2
    rewind: int = 2
    max_lag_blocks: int = 60
    max_block_age: int = 180
    max_future_skew: int = 30
    max_pages: int = 10

    def __post_init__(self) -> None:
        for url in (self.rpc_url, self.graph_url):
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Sources require HTTPS without userinfo")
        if not (1 <= self.confirmations <= self.rewind <= 1000):
            raise ValueError("Unsafe confirmation/rewind bounds")
        if not (
            1 <= self.max_pages <= 100
            and 1 <= self.max_lag_blocks <= 1000
            and 1 <= self.max_block_age <= 3600
            and 0 <= self.max_future_skew <= 60
        ):
            raise ValueError("Unsafe source bounds")


class Reader(Protocol):
    def identity(self) -> None: ...
    def head(self) -> int: ...
    def block(self, number: int) -> dict[str, Any]: ...
    def paused(self, number: int) -> bool: ...
    def verify(self, event: Withdrawal) -> dict[str, Any]: ...


def quantity(value: object) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError("Invalid RPC quantity")
    return int(value, 16)


class ReadRpc:
    """Explicit RPC read allowlist. No key, account, signing or send interface."""

    def __init__(self, url: str, client: httpx.Client) -> None:
        self.url, self.client = url, client

    def _read(self, method: str, params: list[Any]) -> str | dict[str, Any]:
        if method not in {
            "eth_chainId",
            "eth_blockNumber",
            "eth_getBlockByNumber",
            "eth_getCode",
            "eth_call",
            "eth_getTransactionReceipt",
        }:
            raise ValueError("Unsupported RPC method")
        response = self.client.post(
            self.url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=20,
        )
        response.raise_for_status()
        if len(response.content) > 1_000_000:
            raise ValueError("RPC response too large")
        raw = response.json()
        if not isinstance(raw, dict) or raw.get("error") or "result" not in raw:
            raise ValueError("Invalid RPC response")
        result = raw["result"]
        if not isinstance(result, (str, dict)):
            raise ValueError("RPC result unavailable")
        return result

    def identity(self) -> None:
        if quantity(self._read("eth_chainId", [])) != CHAIN_ID:
            raise ValueError("Unsupported chain")
        for address in (VAULT, GUARDIAN):
            if self._read("eth_getCode", [address, "latest"]) in (None, "0x", "0x0"):
                raise ValueError("Contract bytecode missing")
        selector = "0x" + Web3.keccak(text="guardian()").hex()[:8]
        value = hex_value(self._read("eth_call", [{"to": VAULT, "data": selector}, "latest"]), 32)
        if value[2:26] != "0" * 24 or "0x" + value[-40:] != GUARDIAN:
            raise ValueError("Vault/Guardian identity disagreement")

    def head(self) -> int:
        return quantity(self._read("eth_blockNumber", []))

    def block(self, number: int) -> dict[str, Any]:
        raw = self._read("eth_getBlockByNumber", [hex(number), False])
        if not isinstance(raw, dict) or int(raw["number"], 16) != number:
            raise ValueError("RPC block unavailable or mismatched")
        return {
            "number": number,
            "hash": hex_value(raw["hash"], 32),
            "timestamp": int(raw["timestamp"], 16),
        }

    def paused(self, number: int) -> bool:
        result = quantity(
            self._read("eth_call", [{"to": GUARDIAN, "data": "0x5c975abb"}, hex(number)])
        )
        if result not in (0, 1):
            raise ValueError("Invalid Guardian pause state")
        return bool(result)

    def verify(self, event: Withdrawal) -> dict[str, Any]:
        receipt = self._read("eth_getTransactionReceipt", [event.tx_hash])
        if not isinstance(receipt, dict) or int(receipt["status"], 16) != 1:
            raise ValueError("Successful receipt missing")
        if (
            hex_value(receipt["transactionHash"], 32) != event.tx_hash
            or int(receipt["blockNumber"], 16) != event.block
            or hex_value(receipt["blockHash"], 32) != event.block_hash
        ):
            raise ValueError("Receipt does not match source")
        logs = [log for log in receipt["logs"] if int(log["logIndex"], 16) == event.log_index]
        if len(logs) != 1:
            raise ValueError("Canonical receipt log missing")
        log = logs[0]
        topics = log["topics"]
        signature = (
            "0x" + Web3.keccak(text="Withdrawal(address,address,address,uint256,uint256)").hex()
        )
        if (
            hex_value(log["address"], 20) != VAULT
            or log.get("removed") is True
            or len(topics) != 4
            or hex_value(topics[0], 32) != signature
            or hex_value(topics[1], 32)[2:] != "0" * 24 + event.actor[2:]
        ):
            raise ValueError("Receipt withdrawal identity mismatch")
        data = hex_value(log["data"], 64)
        if int(data[2:66], 16) != event.amount:
            raise ValueError("Receipt withdrawal amount mismatch")
        return {
            "receipt_status": 1,
            "block_hash": event.block_hash,
            "transaction_hash": event.tx_hash,
            "log_index": event.log_index,
            "recipient": "0x" + hex_value(topics[2], 32)[-40:],
            "triggered_by": "0x" + hex_value(topics[3], 32)[-40:],
            "remaining_credit": str(int(data[66:], 16)),
        }


class Observer:
    def __init__(
        self, config: ObserveConfig, store: ReviewStore, reader: Reader, client: httpx.Client
    ) -> None:
        self.config, self.store, self.reader, self.client = config, store, reader, client
        store.bind(
            {
                "chain_id": CHAIN_ID,
                "vault": VAULT,
                "guardian": GUARDIAN,
                "deployment": DEPLOYMENT,
                "graph_url": config.graph_url,
                "rpc_origin": urlsplit(config.rpc_url).hostname,
                "origin": "live_graph_rpc",
            }
        )

    def _query(self, query: str, variables: dict[str, str | int]) -> dict[str, Any]:
        response = self.client.post(
            self.config.graph_url, json={"query": query, "variables": variables}, timeout=20
        )
        response.raise_for_status()
        if len(response.content) > 1_000_000:
            raise ValueError("Graph response too large")
        raw = response.json()
        if not isinstance(raw, dict) or raw.get("errors") or not isinstance(raw.get("data"), dict):
            raise ValueError("Invalid Graph response")
        data: dict[str, Any] = raw["data"]
        meta = data["_meta"]
        if meta.get("hasIndexingErrors") is not False or meta.get("deployment") != DEPLOYMENT:
            raise ValueError("Unexpected or unhealthy Graph deployment")
        height = int(meta["block"]["number"])
        if height < 0 or hex_value(meta["block"]["hash"], 32) != self.reader.block(height)["hash"]:
            raise ValueError("Graph/RPC block disagreement")
        return data

    def poll(self) -> dict[str, Any]:
        config = self.config
        checked_at = utc_now()
        try:
            self.reader.identity()
            snapshot = int(self._query(META, {})["_meta"]["block"]["number"])
            head = self.reader.head()
            block = self.reader.block(snapshot)
            age = datetime.now(UTC).timestamp() - block["timestamp"]
            if (
                not 0 <= head - snapshot <= config.max_lag_blocks
                or not -config.max_future_skew <= age <= config.max_block_age
            ):
                raise ValueError("Graph/RPC source is stale or inconsistent")
            through = min(snapshot, head) - config.confirmations + 1
            previous_health = self.store.metadata("health") or {}
            if through < int(previous_health.get("confirmed_through", 0)):
                raise ValueError("Confirmed source head regressed")
            cursor = self.store.cursor()
            after = -1 if cursor is None else max(0, cursor[1] - config.rewind) * 1_000_000 - 1
            if previous_health.get("status") == "catching_up":
                after = int(previous_health["next_after"])
            added = 0
            complete = False
            for _ in range(config.max_pages):
                data = self._query(
                    QUERY, {"after": str(after), "through": str(through), "snapshot": block["hash"]}
                )
                if int(data["_meta"]["block"]["number"]) != snapshot:
                    raise ValueError("Graph snapshot changed")
                raw_rows = data["withdrawals"]
                if not isinstance(raw_rows, list) or len(raw_rows) > 100:
                    raise ValueError("Invalid Graph page")
                validated: list[dict[str, Any]] = []
                for raw in raw_rows:
                    ev = Withdrawal.parse(raw)
                    if (
                        ev.sequence <= after
                        or ev.block > through
                        or not 0 < ev.amount < 2**256
                        or self.reader.block(ev.block)["hash"] != ev.block_hash
                        or self.reader.block(ev.block)["timestamp"] != ev.timestamp
                    ):
                        raise ValueError("Unordered, unconfirmed or noncanonical withdrawal")
                    proof = self.reader.verify(ev)
                    if (
                        raw["recipient"].lower() != proof["recipient"]
                        or raw["triggeredBy"].lower() != proof["triggered_by"]
                        or str(raw["remainingCredit"]) != proof["remaining_credit"]
                    ):
                        raise ValueError("Graph fields disagree with receipt")
                    proof |= {
                        "rpc_head": head,
                        "confirmations": head - ev.block + 1,
                        "graph_snapshot": snapshot,
                        "verified_at": checked_at,
                    }
                    validated.append({"raw": raw, "proof": proof, "origin": "live_graph_rpc"})
                    after = ev.sequence
                added += self.store.ingest(validated)
                if len(raw_rows) < 100:
                    complete = True
                    break
            # Recheck the snapshot after potentially long paging/receipt reads.
            if self.reader.block(snapshot)["hash"] != block["hash"]:
                raise ValueError("Snapshot reorg during observation")
            health = {
                "status": "healthy" if complete else "catching_up",
                "checked_at": checked_at,
                "rpc_head": head,
                "graph_snapshot": snapshot,
                "block_age_seconds": int(age),
                "confirmed_through": through,
                "snapshot_hash": block["hash"],
                "guardian_paused": self.reader.paused(snapshot),
                "state_block": snapshot,
                "added": added,
                "scan_complete": complete,
                "next_after": str(after),
                "max_future_clock_skew_seconds": config.max_future_skew,
                "limits": [
                    "Bounded Graph pagination; provider omissions cannot be disproved.",
                    "Canonical replay covers the configured rewind window.",
                ],
            }
            self.store.health(health)
            return health
        except Exception as exc:
            old = self.store.metadata("health") or {}
            self.store.health(
                {
                    **old,
                    "status": "degraded",
                    "checked_at": checked_at,
                    "scan_complete": False,
                    "error_type": type(exc).__name__,
                    "gap": "Source verification failed; stored evidence may be stale.",
                }
            )
            raise
