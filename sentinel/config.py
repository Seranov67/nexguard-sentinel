"""Explicit runtime settings; credentials never enter serialized state."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    rpc_http: str
    subgraph_url: str
    guardian_address: str
    vault_address: str
    state_path: Path
    chain_id: int = 84532
    confirmations: int = 2
    rewind_blocks: int = 2
    graph_deployment: str = "QmNcPyyo2Ybz1M3Lmg1eAE8A6ATuhZ3RvqePiks18fTfcQ"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        """Read only the supported runtime fields, not signing credentials."""

        def required(name: str) -> str:
            value = env.get(name, "").strip()
            if not value:
                raise ValueError(f"{name} is required")
            return value

        def endpoint(name: str) -> str:
            value = required(name)
            parsed = urlsplit(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError(f"{name} must be an HTTPS endpoint without userinfo")
            return value

        def address(name: str) -> str:
            value = required(name).lower()
            if len(value) != 42 or not value.startswith("0x"):
                raise ValueError(f"{name} must be an Ethereum address")
            try:
                number = int(value[2:], 16)
            except ValueError:
                raise ValueError(f"{name} must be an Ethereum address") from None
            if number == 0:
                raise ValueError(f"{name} cannot be zero")
            return value

        chain = int(env.get("CHAIN_ID", "84532"))
        confirmations = int(env.get("SENTINEL_CONFIRMATIONS", "2"))
        rewind = int(env.get("SENTINEL_REWIND_BLOCKS", "2"))
        if chain != 84532:
            raise ValueError("Only Base Sepolia chain 84532 is supported")
        if confirmations < 1 or rewind < confirmations:
            raise ValueError("Require confirmations >= 1 and rewind >= confirmations")
        state = env.get("SENTINEL_STATE_PATH", ".sentinel/state.sqlite3").strip()
        if not state or state == ":memory:":
            raise ValueError("A durable state path is required")
        return cls(
            endpoint("RPC_HTTP"),
            endpoint("SUBGRAPH_URL"),
            address("GUARDIAN_ADDRESS"),
            address("VAULT_ADDRESS"),
            Path(state),
            chain,
            confirmations,
            rewind,
        )
