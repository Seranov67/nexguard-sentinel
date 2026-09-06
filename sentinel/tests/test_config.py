import pytest

from sentinel.config import Settings


def environment() -> dict[str, str]:
    return {
        "RPC_HTTP": "https://sepolia.base.org",
        "SUBGRAPH_URL": "https://example.org/query",
        "GUARDIAN_ADDRESS": "0x" + "12" * 20,
        "VAULT_ADDRESS": "0x" + "34" * 20,
    }


def test_config_defaults() -> None:
    settings = Settings.from_env(environment())
    assert settings.chain_id == 84532
    assert settings.confirmations == settings.rewind_blocks == 2


@pytest.mark.parametrize(
    "key,value",
    [
        ("CHAIN_ID", "1"),
        ("GUARDIAN_ADDRESS", "0x" + "00" * 20),
        ("RPC_HTTP", "http://example.org"),
        ("SUBGRAPH_URL", ""),
        ("SENTINEL_STATE_PATH", ":memory:"),
        ("SENTINEL_CONFIRMATIONS", "0"),
        ("SENTINEL_REWIND_BLOCKS", "1"),
        ("VAULT_ADDRESS", "invalid"),
    ],
)
def test_unsafe_config_rejected(key: str, value: str) -> None:
    env = environment()
    env[key] = value
    with pytest.raises(ValueError):
        Settings.from_env(env)
