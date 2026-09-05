"""Tests for Ledger integration (ERC-7730 Clear Signing and unpause CLI)."""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sentinel.ledger.keyring_helper import (
    check_installed,
    cmd_check,
    cmd_enroll,
    cmd_export_env,
    cmd_get,
    cmd_list,
)
from sentinel.ledger.unpause_ledger import (
    CHAIN_ID,
    GUARDIAN_ADDRESS,
    _build_calldata,
    _function_selector,
    _keccak256_reason,
    _load_erc7730,
    _print_ledger_screen,
    _validate_erc7730,
    dry_run,
    simulate,
)

# ---------------------------------------------------------------------------
# Ledger Unpause CLI & Calldata Tests
# ---------------------------------------------------------------------------


def test_chain_id_and_guardian_address() -> None:
    assert CHAIN_ID == 84532
    assert GUARDIAN_ADDRESS.startswith("0x")
    assert len(GUARDIAN_ADDRESS) == 42


def test_keccak256_reason_format() -> None:
    reason_hash = _keccak256_reason("Protocol incident resolved safely")
    assert reason_hash.startswith("0x")
    assert len(reason_hash) == 66  # "0x" + 64 hex characters


def test_function_selector() -> None:
    selector = _function_selector("unpause(bytes32)")
    assert selector.startswith("0x")
    assert len(selector) == 10  # "0x" + 8 hex chars


def test_build_calldata() -> None:
    reason_hash = _keccak256_reason("Operational review completed")
    calldata = _build_calldata(reason_hash)
    assert calldata.startswith("0x")
    # 4-byte selector (8 chars) + 32-byte reason hash (64 chars) = 72 hex chars + "0x" prefix = 74
    assert len(calldata) == 74


def test_erc7730_descriptor_valid() -> None:
    descriptor = _load_erc7730()
    assert isinstance(descriptor, dict)
    issues = _validate_erc7730(descriptor)
    assert issues == []


def test_erc7730_missing_fields_validation() -> None:
    bad_descriptor: dict[str, Any] = {"context": {}}
    issues = _validate_erc7730(bad_descriptor)
    assert len(issues) > 0


def test_print_ledger_screen_output(capsys: pytest.CaptureFixture[str]) -> None:
    reason = "Incident investigated and node restored"
    reason_hash = _keccak256_reason(reason)
    _print_ledger_screen(reason, reason_hash)
    out = capsys.readouterr().out
    assert "LEDGER DEVICE SCREEN" in out
    assert "Base Sepolia" in out
    assert '0x8B7B' in out
    assert "APPROVE" in out


def test_simulate_mode(capsys: pytest.CaptureFixture[str]) -> None:
    simulate("Normal post-incident recovery")
    out = capsys.readouterr().out
    assert "SIMULATE" in out
    assert "ERC-7730" in out
    assert "0x" in out


def test_dry_run_mode(capsys: pytest.CaptureFixture[str]) -> None:
    dry_run("Normal post-incident recovery")
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "cast send" in out
    assert "--ledger" in out


# ---------------------------------------------------------------------------
# Ledger Key Ring Helper Tests
# ---------------------------------------------------------------------------


def test_keyring_check_installed() -> None:
    result = check_installed()
    assert isinstance(result, bool)


@patch("sentinel.ledger.keyring_helper.check_installed", return_value=True)
@patch("subprocess.run")
def test_keyring_cmd_check_output(
    mock_run: MagicMock, mock_check: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["wallet-cli"], returncode=0, stdout="wallet-cli 1.0.0", stderr=""
    )
    cmd_check()
    out = capsys.readouterr().out
    assert "wallet-cli found" in out


@patch("sentinel.ledger.keyring_helper.check_installed", return_value=True)
@patch("sentinel.ledger.keyring_helper._run")
def test_keyring_cmd_enroll(
    mock_run: MagicMock, mock_check: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["wallet-cli"], returncode=0, stdout="Enrolled OK", stderr=""
    )
    cmd_enroll("TEST_SECRET_KEY")
    out = capsys.readouterr().out
    assert "Enrolled" in out or "enrolled" in out
    mock_run.assert_called_once()


@patch("sentinel.ledger.keyring_helper.check_installed", return_value=True)
@patch("sentinel.ledger.keyring_helper._run")
def test_keyring_cmd_get(
    mock_run: MagicMock, mock_check: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["wallet-cli"], returncode=0, stdout="my_secret_value", stderr=""
    )
    cmd_get("TEST_SECRET_KEY")
    out = capsys.readouterr().out
    assert "my_secret_value" in out
    mock_run.assert_called_once()


@patch("sentinel.ledger.keyring_helper.check_installed", return_value=True)
@patch("sentinel.ledger.keyring_helper._run")
def test_keyring_cmd_list(
    mock_run: MagicMock, mock_check: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["wallet-cli"], returncode=0, stdout="RPC_HTTP\nPRIVATE_KEY", stderr=""
    )
    cmd_list()
    out = capsys.readouterr().out
    assert "RPC_HTTP" in out
    assert "PRIVATE_KEY" in out
    mock_run.assert_called_once()


@patch("sentinel.ledger.keyring_helper.check_installed", return_value=True)
@patch("sentinel.ledger.keyring_helper._run")
def test_keyring_cmd_export_env(
    mock_run: MagicMock, mock_check: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["wallet-cli"], returncode=0, stdout="https://sepolia.base.org", stderr=""
    )
    cmd_export_env()
    out = capsys.readouterr().out
    assert "export RPC_HTTP" in out
