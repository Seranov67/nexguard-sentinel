from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams, TxReceipt

BASE_SEPOLIA_CHAIN_ID = 84532
ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Deployment:
    name: str
    address: ChecksumAddress
    transaction_hash: str
    block_number: int


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def checksum_address(name: str) -> ChecksumAddress:
    value = required_env(name)
    if not Web3.is_address(value):
        raise RuntimeError(f"{name} must be a valid address")
    return Web3.to_checksum_address(value)


def load_artifact(contract_name: str) -> dict[str, Any]:
    path = CONTRACTS / "out" / f"{contract_name}.sol" / f"{contract_name}.json"
    if not path.is_file():
        raise RuntimeError(f"Missing {path}; run `cd contracts && forge build` first")
    parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


def fee_fields(web3: Web3) -> tuple[int, int]:
    pending = web3.eth.get_block("pending")
    base_fee = pending.get("baseFeePerGas")
    if base_fee is None:
        raise RuntimeError("RPC pending block does not expose EIP-1559 baseFeePerGas")
    priority_fee = int(web3.eth.max_priority_fee)
    return int(base_fee) * 2 + priority_fee, priority_fee


def validate_chain(actual_chain: int) -> None:
    if actual_chain != BASE_SEPOLIA_CHAIN_ID:
        raise RuntimeError(
            f"Refusing deployment: expected chain {BASE_SEPOLIA_CHAIN_ID}, got {actual_chain}"
        )


def validate_roles(owner: ChecksumAddress, keeper: ChecksumAddress) -> None:
    if owner == keeper:
        raise RuntimeError("OWNER_ADDRESS and KEEPER_ADDRESS must differ")


def deploy_contract(
    web3: Web3,
    account: LocalAccount,
    contract_name: str,
    constructor_args: tuple[ChecksumAddress, ...],
    nonce: int,
) -> Deployment:
    artifact = load_artifact(contract_name)
    bytecode = artifact["bytecode"]["object"]
    if not isinstance(bytecode, str) or not bytecode.startswith("0x"):
        raise RuntimeError(f"Invalid bytecode in {contract_name} artifact")

    factory: type[Contract] = web3.eth.contract(abi=artifact["abi"], bytecode=bytecode)
    max_fee, priority_fee = fee_fields(web3)
    transaction: TxParams = factory.constructor(*constructor_args).build_transaction(
        {
            "chainId": BASE_SEPOLIA_CHAIN_ID,
            "from": account.address,
            "nonce": nonce,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }
    )
    estimated_gas = web3.eth.estimate_gas(transaction)
    transaction["gas"] = estimated_gas * 120 // 100

    transaction_dict: dict[str, Any] = dict(transaction)
    signed = account.sign_transaction(transaction_dict)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    public_hash = tx_hash.hex()
    print(
        json.dumps(
            {"event": "deployment_broadcast", "contract": contract_name, "tx": public_hash}
        )
    )

    receipt: TxReceipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    contract_address = receipt.get("contractAddress")
    if int(receipt["status"]) != 1 or contract_address is None:
        raise RuntimeError(f"{contract_name} deployment failed: {public_hash}")

    address = Web3.to_checksum_address(contract_address)
    return Deployment(contract_name, address, public_hash, int(receipt["blockNumber"]))


def verify_deployment(
    web3: Web3,
    guardian_deployment: Deployment,
    vault_deployment: Deployment,
    owner: ChecksumAddress,
    keeper: ChecksumAddress,
) -> None:
    guardian_artifact = load_artifact("Guardian")
    vault_artifact = load_artifact("DemoVault")
    guardian = web3.eth.contract(
        address=guardian_deployment.address, abi=guardian_artifact["abi"]
    )
    vault = web3.eth.contract(address=vault_deployment.address, abi=vault_artifact["abi"])

    if guardian.functions.owner().call() != owner:
        raise RuntimeError("Guardian owner verification failed")
    if guardian.functions.keepers(keeper).call() is not True:
        raise RuntimeError("Guardian keeper verification failed")
    if guardian.functions.paused().call() is not False:
        raise RuntimeError("Guardian unexpectedly starts paused")
    if vault.functions.guardian().call() != guardian_deployment.address:
        raise RuntimeError("DemoVault Guardian verification failed")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy NexGuard demo contracts to Base Sepolia")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env.ethonline")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    load_dotenv(args.env_file)
    web3 = Web3(Web3.HTTPProvider(required_env("RPC_HTTP"), request_kwargs={"timeout": 20}))
    actual_chain = web3.eth.chain_id
    validate_chain(actual_chain)

    account: LocalAccount = web3.eth.account.from_key(required_env("DEPLOYER_PRIVATE_KEY"))
    owner = checksum_address("OWNER_ADDRESS")
    keeper = checksum_address("KEEPER_ADDRESS")
    validate_roles(owner, keeper)

    nonce = web3.eth.get_transaction_count(account.address, "pending")
    guardian = deploy_contract(web3, account, "Guardian", (owner, keeper), nonce)
    vault = deploy_contract(web3, account, "DemoVault", (guardian.address,), nonce + 1)
    verify_deployment(web3, guardian, vault, owner, keeper)

    evidence = {
        "schemaVersion": 1,
        "verifiedAt": datetime.now(UTC).isoformat(),
        "chainId": actual_chain,
        "deployer": account.address,
        "owner": owner,
        "keeper": keeper,
        "contracts": [asdict(guardian), asdict(vault)],
        "verification": {
            "guardianOwner": True,
            "keeperEnabled": True,
            "guardianInitiallyUnpaused": True,
            "vaultReadsGuardian": True,
        },
    }
    if args.evidence is not None:
        atomic_write_json(args.evidence, evidence)
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
