import { BigInt } from "@graphprotocol/graph-ts";

import { Withdrawal as WithdrawalEvent } from "../generated/DemoVault/DemoVault";
import { Withdrawal } from "../generated/schema";

const LOGS_PER_BLOCK = BigInt.fromI32(1_000_000);

export function handleWithdrawal(event: WithdrawalEvent): void {
  const entity = new Withdrawal(
    event.transaction.hash.concatI32(event.logIndex.toI32()),
  );

  entity.sequence = event.block.number.times(LOGS_PER_BLOCK).plus(event.logIndex);
  entity.blockNumber = event.block.number;
  entity.blockHash = event.block.hash;
  entity.transactionHash = event.transaction.hash;
  entity.logIndex = event.logIndex;
  entity.timestamp = event.block.timestamp;
  entity.who = event.params.account;
  entity.recipient = event.params.recipient;
  entity.triggeredBy = event.params.triggeredBy;
  entity.amount = event.params.amount;
  entity.remainingCredit = event.params.remainingCredit;
  entity.save();
}
