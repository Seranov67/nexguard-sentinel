# Sentinel runtime

See the root README for installation and CLI examples. Python 3.12 is required;
`requirements.lock` records the complete tested environment.

The Graph Ingestor validates deployment, canonical snapshot hash, confirmation
window, ordering and entity identity before persistence. The read cursor and
processed-event bookkeeping are separate, so a crash after ingest does not lose
work. A historical `the_graph_withdrawals` source is normalized on migration;
existing intent ownership continues to prevent repeat actions.

The rolling feature window includes previously assessed events. Only newly pending
events enter a new reservation. AI receives numeric features, has no signer access,
and must produce strict validated output. Classification traces record model,
prompt version/hash, inputs and result. No model means no action.

Reservations serialize deduplication, cooldown (300 seconds) and budget (3 per
600 seconds). An unfinished intent blocks further action. The signed transaction
hash is durable before broadcast; receipt verification checks canonical block,
confirmation depth, intended call and final state. Reconciliation never resends.
A reset is attributed and does not erase event ownership or action limits.

Dry-run creates an isolated preview store. It cannot consume live pending events
or create simulated success records in the live database. Storage failures stop
the process. Outbox worker failures are independent; delivery is leased,
at-least-once, and bounded to three attempts with terminal status visible in CLI.

Evidence/MCP verify payload consistency, not provider authenticity. Payment is a
prototype; fake proofs are rejected. Ledger simulation is explicitly labelled;
no hardware Clear Signing claim is made without device evidence.
