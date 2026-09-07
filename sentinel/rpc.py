"""Base Sepolia RPC adapter with a lazy, pause-only keeper signer."""

import json
from collections.abc import Callable
from typing import Any

from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxParams, Wei

from sentinel.config import Settings
from sentinel.executor import Receipt, SignedPause

# Deliberately excludes owner operations and arbitrary write methods.
GUARDIAN_ABI: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": name,
        "stateMutability": "view",
        "inputs": inputs,
        "outputs": [{"type": output, "name": ""}],
    }
    for name, inputs, output in [
        ("paused", [], "bool"),
        ("owner", [], "address"),
        ("keepers", [{"name": "keeper", "type": "address"}], "bool"),
    ]
] + [
    {
        "type": "function",
        "name": "pause",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "incidentRef", "type": "bytes32"},
            {"name": "severity", "type": "uint8"},
        ],
        "outputs": [],
    },
    {
        "type": "event",
        "name": "Paused",
        "anonymous": False,
        "inputs": [
            {"name": "incidentRef", "type": "bytes32", "indexed": True},
            {"name": "severity", "type": "uint8", "indexed": False},
            {"name": "keeper", "type": "address", "indexed": True},
        ],
    },
]
VAULT_ABI = [
    {
        "type": "function",
        "name": "guardian",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "address", "name": ""}],
    }
]


def public_hex(value: bytes) -> str:
    return "0x" + value.hex()


class RpcChain:
    def __init__(
        self, settings: Settings, key: Callable[[], str] | None = None, web3: Web3 | None = None
    ) -> None:
        self.settings, self.key = settings, key
        self.web3 = web3 or Web3(
            Web3.HTTPProvider(settings.rpc_http, request_kwargs={"timeout": 20})
        )
        self.guardian = self.web3.eth.contract(
            address=Web3.to_checksum_address(settings.guardian_address), abi=GUARDIAN_ABI
        )
        self.vault = self.web3.eth.contract(
            address=Web3.to_checksum_address(settings.vault_address), abi=VAULT_ABI
        )

    def identity(self) -> tuple[int, str, str]:
        chain = self.web3.eth.chain_id
        if chain != 84532:
            raise ValueError("Only Base Sepolia is allowed")
        if (
            not self.web3.eth.get_code(self.guardian.address)
            or not self.web3.eth.get_code(self.vault.address)
            or str(self.vault.functions.guardian().call()).lower()
            != self.settings.guardian_address.lower()
        ):
            raise ValueError("Contract identity verification failed")
        return chain, self.settings.guardian_address, self.settings.vault_address

    def head(self) -> int:
        return self.web3.eth.block_number

    def block_hash(self, block: int) -> str:
        value = self.web3.eth.get_block(block).get("hash")
        if value is None:
            raise ValueError("RPC block hash unavailable")
        return public_hex(value)

    def paused(self, block: int | None = None) -> bool:
        value = self.guardian.functions.paused().call(
            block_identifier="latest" if block is None else block
        )
        if not isinstance(value, bool):
            raise ValueError("Invalid Guardian state")
        return value

    def sign_pause(self, ref: str, severity: int) -> SignedPause:
        self.identity()
        if self.key is None or severity != 3:
            raise ValueError("Pause signer unavailable or invalid severity")
        account: LocalAccount = self.web3.eth.account.from_key(self.key())
        if (
            str(self.guardian.functions.owner().call()).lower() == account.address.lower()
            or self.guardian.functions.keepers(account.address).call() is not True
        ):
            raise ValueError("Signer must be an authorized non-owner keeper")
        nonce = self.web3.eth.get_transaction_count(account.address, "pending")
        pending = self.web3.eth.get_block("pending")
        base_fee = pending.get("baseFeePerGas")
        if base_fee is None:
            raise ValueError("EIP-1559 fees unavailable")
        tip = self.web3.eth.max_priority_fee
        fees = {"maxFeePerGas": int(base_fee) * 2 + tip, "maxPriorityFeePerGas": tip}
        parameters: TxParams = {
            "chainId": 84532,
            "from": account.address,
            "nonce": nonce,
            "value": Wei(0),
            "maxFeePerGas": Wei(fees["maxFeePerGas"]),
            "maxPriorityFeePerGas": Wei(fees["maxPriorityFeePerGas"]),
        }
        tx = self.guardian.functions.pause(bytes.fromhex(ref[2:]), severity).build_transaction(
            parameters
        )
        tx["gas"] = self.web3.eth.estimate_gas(tx) * 120 // 100
        transaction: dict[str, Any] = dict(tx)
        signed = account.sign_transaction(transaction)
        return SignedPause(
            nonce,
            json.dumps(fees, sort_keys=True),
            public_hex(signed.hash),
            bytes(signed.raw_transaction),
        )

    def send(self, signed: SignedPause) -> str:
        self.identity()
        return public_hex(self.web3.eth.send_raw_transaction(signed.raw))

    def receipt(self, tx_hash: str) -> Receipt | None:
        try:
            receipt = self.web3.eth.get_transaction_receipt(HexBytes(tx_hash))
        except TransactionNotFound:
            return None
        proof, severity = None, None
        for log in receipt["logs"]:
            if str(log["address"]).lower() != self.settings.guardian_address.lower():
                continue
            topic = Web3.keccak(text="Paused(bytes32,uint8,address)")
            if not log["topics"] or log["topics"][0] != topic:
                continue
            parsed = self.guardian.events.Paused().process_log(log)
            if proof is not None:
                raise ValueError("Multiple pause proofs in one receipt")
            proof = public_hex(parsed["args"]["incidentRef"])
            severity = int(parsed["args"]["severity"])
        return Receipt(
            public_hex(receipt["transactionHash"]),
            int(receipt["blockNumber"]),
            public_hex(receipt["blockHash"]),
            int(receipt["status"]),
            proof,
            severity,
        )
