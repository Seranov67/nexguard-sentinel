from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TransactionNotFound

from sentinel.rpc import GUARDIAN_ABI, RpcChain
from sentinel.tests.test_action_loop import BLOCK, GUARDIAN, TX, VAULT


@pytest.fixture
def rpc(setup):
    settings, _, _, _, _ = setup
    web3 = Mock()
    guardian, vault = Mock(), Mock()
    guardian.address, vault.address = GUARDIAN, VAULT
    web3.eth.contract.side_effect = [guardian, vault]
    web3.eth.chain_id = 84532
    web3.eth.get_code.return_value = b"contract"
    vault.functions.guardian.return_value.call.return_value = GUARDIAN
    guardian.functions.owner.return_value.call.return_value = "0x" + "77" * 20
    guardian.functions.keepers.return_value.call.return_value = True
    guardian.functions.paused.return_value.call.return_value = False
    account = web3.eth.account.from_key.return_value
    account.address = "0x" + "88" * 20
    account.sign_transaction.return_value = SimpleNamespace(
        hash=bytes.fromhex(TX[2:]), raw_transaction=b"signed"
    )
    web3.eth.get_transaction_count.return_value = 9
    web3.eth.get_block.return_value = {"baseFeePerGas": 100, "hash": HexBytes(BLOCK)}
    web3.eth.max_priority_fee = 2
    web3.eth.estimate_gas.return_value = 50_000
    guardian.functions.pause.return_value.build_transaction.return_value = {"nonce": 9}
    key = Mock(return_value="ephemeral-test-key-provider")
    return RpcChain(settings, key, web3), web3, guardian, vault, key


def test_rpc_signer_is_lazy_and_only_builds_zero_value_pause(rpc):
    chain, web3, guardian, _, key = rpc
    chain.identity()
    key.assert_not_called()
    signed = chain.sign_pause(TX, 3)
    assert signed.tx_hash == TX and signed.nonce == 9 and signed.raw == b"signed"
    guardian.functions.pause.assert_called_once_with(bytes.fromhex(TX[2:]), 3)
    params = guardian.functions.pause.return_value.build_transaction.call_args.args[0]
    assert params["chainId"] == 84532 and params["value"] == 0
    assert params["maxFeePerGas"] == 202 and params["nonce"] == 9
    web3.eth.send_raw_transaction.assert_not_called()
    web3.eth.send_raw_transaction.return_value = HexBytes(TX)
    assert chain.send(signed) == TX
    web3.eth.send_raw_transaction.assert_called_once_with(b"signed")
    assert {
        item["name"] for item in GUARDIAN_ABI if item.get("stateMutability") == "nonpayable"
    } == {"pause"}


@pytest.mark.parametrize("failure", ["mainnet", "owner", "not_keeper", "wrong_vault", "no_code"])
def test_rpc_refuses_unsafe_identity_or_signer(rpc, failure):
    chain, web3, guardian, vault, key = rpc
    if failure == "mainnet":
        web3.eth.chain_id = 1
    elif failure == "owner":
        guardian.functions.owner.return_value.call.return_value = (
            web3.eth.account.from_key.return_value.address
        )
    elif failure == "not_keeper":
        guardian.functions.keepers.return_value.call.return_value = False
    elif failure == "wrong_vault":
        vault.functions.guardian.return_value.call.return_value = VAULT
    else:
        web3.eth.get_code.return_value = b""
    with pytest.raises(ValueError):
        chain.sign_pause(TX, 3)
    web3.eth.account.from_key.return_value.sign_transaction.assert_not_called()
    web3.eth.send_raw_transaction.assert_not_called()
    if failure in ("mainnet", "wrong_vault", "no_code"):
        key.assert_not_called()


def test_read_only_adapter_cannot_access_signer(rpc):
    chain, _, _, _, key = rpc
    chain.key = None
    with pytest.raises(ValueError, match="unavailable"):
        chain.sign_pause(TX, 3)
    key.assert_not_called()


def test_receipt_decodes_real_pause_event_and_ignores_other_contracts(rpc):
    chain, web3, _, _, _ = rpc
    chain.guardian = Web3().eth.contract(
        address=Web3.to_checksum_address(GUARDIAN), abi=GUARDIAN_ABI
    )
    log = {
        "address": GUARDIAN,
        "topics": [
            Web3.keccak(text="Paused(bytes32,uint8,address)"),
            HexBytes(TX),
            HexBytes("0x" + "00" * 12 + "88" * 20),
        ],
        "data": HexBytes((3).to_bytes(32, "big")),
        "blockNumber": 100,
        "blockHash": HexBytes(BLOCK),
        "transactionHash": HexBytes(TX),
        "transactionIndex": 0,
        "logIndex": 0,
    }
    web3.eth.get_transaction_receipt.return_value = {
        "transactionHash": HexBytes(TX),
        "blockHash": HexBytes(BLOCK),
        "blockNumber": 100,
        "status": 1,
        "logs": [{**log, "address": VAULT}, log],
    }
    receipt = chain.receipt(TX)
    assert receipt.incident_ref == TX and receipt.severity == 3 and receipt.status == 1
    web3.eth.get_transaction_receipt.side_effect = TransactionNotFound("not mined")
    assert chain.receipt(TX) is None
