# Sentinel incident-investigation Recipe

The stdio MCP server calls the local Evidence API at `EVIDENCE_API_URL`.
For the prototype server, set `SENTINEL_EVIDENCE_DEMO=1`; the MCP client sends
`X-Dev-Mode: 1`. No real payment verifier is implemented. Other requests receive
402; arbitrary payment proofs never grant access.

`get_latest_incident` returns `found`, incident ID, UTC creation time, durable
intent status, recorded trigger cause, pause evidence, contract addresses, chain
ID, fingerprint and source-event count. Historical records without classification
traces explicitly report that absence rather than inventing an AI explanation.

`verify_incident_evidence(incident_id)` fetches the record, recomputes its canonical
SHA-256 fingerprint and checks basic status/chain consistency. `verified=true`
means payload integrity only. It does not authenticate the server or independently
verify a transaction onchain. Agents should quote this scope and any issues.

The Recipe tells agents to retrieve, verify and explain the recorded cause without
inventing missing evidence. The real-model A/B runner exposes the same tools and
task in both conditions, adding Recipe guidance only to the treatment. It saves
actual tool calls and structural checks. Explanation accuracy needs human review.
No synthetic benchmark scores or settled-payment claims are valid evidence.
