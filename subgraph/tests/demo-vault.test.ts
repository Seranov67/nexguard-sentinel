import {
  afterAll,
  assert,
  beforeAll,
  clearStore,
  newMockEvent,
  test,
} from "matchstick-as/assembly/index";
import { Address, BigInt, Bytes, ethereum } from "@graphprotocol/graph-ts";

import { Withdrawal as WithdrawalEvent } from "../generated/DemoVault/DemoVault";
import { handleWithdrawal } from "../src/demo-vault";

const ACCOUNT = "0x00000000000000000000000000000000000000a1";
const RECIPIENT = "0x00000000000000000000000000000000000000b2";
const TRIGGERED_BY = "0x00000000000000000000000000000000000000c3";
const TX_HASH =
  "0x1111111111111111111111111111111111111111111111111111111111111111";

function createWithdrawalEvent(): WithdrawalEvent {
  const event = changetype<WithdrawalEvent>(newMockEvent());
  event.parameters = new Array<ethereum.EventParam>();
  event.parameters.push(
    new ethereum.EventParam("account", ethereum.Value.fromAddress(Address.fromString(ACCOUNT))),
  );
  event.parameters.push(
    new ethereum.EventParam(
      "recipient",
      ethereum.Value.fromAddress(Address.fromString(RECIPIENT)),
    ),
  );
  event.parameters.push(
    new ethereum.EventParam(
      "triggeredBy",
      ethereum.Value.fromAddress(Address.fromString(TRIGGERED_BY)),
    ),
  );
  event.parameters.push(
    new ethereum.EventParam("amount", ethereum.Value.fromUnsignedBigInt(BigInt.fromI32(70))),
  );
  event.parameters.push(
    new ethereum.EventParam(
      "remainingCredit",
      ethereum.Value.fromUnsignedBigInt(BigInt.fromI32(30)),
    ),
  );
  event.block.number = BigInt.fromI32(123);
  event.block.timestamp = BigInt.fromI32(1_789_000_000);
  event.logIndex = BigInt.fromI32(7);
  event.transaction.hash = Bytes.fromHexString(TX_HASH);
  return event;
}

beforeAll(() => {
  handleWithdrawal(createWithdrawalEvent());
});

afterAll(() => {
  clearStore();
});

test("indexes a Withdrawal with a deterministic cursor", () => {
  const id = Bytes.fromHexString(TX_HASH).concatI32(7).toHexString();

  assert.entityCount("Withdrawal", 1);
  assert.fieldEquals("Withdrawal", id, "sequence", "123000007");
  assert.fieldEquals("Withdrawal", id, "blockNumber", "123");
  assert.fieldEquals("Withdrawal", id, "transactionHash", TX_HASH);
  assert.fieldEquals("Withdrawal", id, "logIndex", "7");
  assert.fieldEquals("Withdrawal", id, "timestamp", "1789000000");
  assert.fieldEquals("Withdrawal", id, "who", ACCOUNT);
  assert.fieldEquals("Withdrawal", id, "recipient", RECIPIENT);
  assert.fieldEquals("Withdrawal", id, "triggeredBy", TRIGGERED_BY);
  assert.fieldEquals("Withdrawal", id, "amount", "70");
  assert.fieldEquals("Withdrawal", id, "remainingCredit", "30");
});
