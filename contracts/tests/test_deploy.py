from __future__ import annotations

import json
from pathlib import Path

import pytest
from eth_typing import ChecksumAddress
from web3 import Web3

from contracts.deploy import (
    BASE_SEPOLIA_CHAIN_ID,
    atomic_write_json,
    checksum_address,
    required_env,
    validate_chain,
    validate_roles,
)


def test_required_env_refuses_missing_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_DEPLOY_VALUE", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_DEPLOY_VALUE is required"):
        required_env("MISSING_DEPLOY_VALUE")


def test_checksum_address_validates_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OWNER_ADDRESS", "not-an-address")
    with pytest.raises(RuntimeError, match="must be a valid address"):
        checksum_address("OWNER_ADDRESS")


def test_validate_chain_accepts_only_base_sepolia() -> None:
    validate_chain(BASE_SEPOLIA_CHAIN_ID)
    with pytest.raises(RuntimeError, match="Refusing deployment"):
        validate_chain(1)


def test_validate_roles_requires_separation() -> None:
    address: ChecksumAddress = Web3.to_checksum_address(
        "0x0000000000000000000000000000000000000001"
    )
    with pytest.raises(RuntimeError, match="must differ"):
        validate_roles(address, address)


def test_atomic_write_json_replaces_complete_document(tmp_path: Path) -> None:
    destination = tmp_path / "deployment.json"
    atomic_write_json(destination, {"chainId": BASE_SEPOLIA_CHAIN_ID})

    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "chainId": BASE_SEPOLIA_CHAIN_ID
    }
    assert not destination.with_suffix(".json.tmp").exists()
