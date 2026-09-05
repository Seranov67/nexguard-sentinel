# NexGuard Sentinel ? API & Protocol Reference

This document provides formal technical specifications for external systems, AI agents, and integration partners interacting with **NexGuard Sentinel**.

---

## 1. Incident Evidence API (REST / OpenAPI)

The Incident Evidence API (`sentinel/evidence_api.py`) exposes cryptographic proof of circuit-breaker actions on Base Sepolia.

### Base URL
- Local: `http://127.0.0.1:8000`
- Production: Protected behind SSL and load-balancer.

### Endpoints

#### 1. `GET /health`
Returns service and database health status. **No payment required.**

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database_reachable": true,
  "latest_incident_id": "inc_6a2d540da0445aa2"
}
```

---

#### 2. `GET /api/v1/incidents/latest`
Returns the most recent incident evidence record, transaction hashes, and cryptographic state fingerprint.

**Security:** Protected by x402/MPP micro-payment gate.
- In production, returns `402 Payment Required` unless a valid `X-Payment-Proof` header is provided.
- In development/testing mode, pass `X-Dev-Mode: 1`.

**Request Headers:**
```http
GET /api/v1/incidents/latest HTTP/1.1
Host: 127.0.0.1:8000
X-Dev-Mode: 1
```

**Response (200 OK):**
```json
{
  "incident_id": "inc_6a2d540da0445aa2",
  "intent_id": "intent_pause_6a2d540da0445aa2",
  "created_at": "2026-09-05T19:22:25.984507+00:00",
  "status": "success",
  "trigger_cause": "Three consecutive Vault withdrawal events above the anomaly threshold triggered the AI classifier (severity=critical, confidence>=0.8). Deterministic ActionPolicy authorized keeper pause.",
  "source_event_ids": [
    "0x05e2c2fad8422867dc97587bb9f4fd8516f616ed41ecd30469738a221d1ae35e28000000"
  ],
  "pause_evidence": {
    "tx_hash": "0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75",
    "block_number": 46433927,
    "explorer_url": "https://sepolia.basescan.org/tx/0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75",
    "nonce": 3,
    "status": "success"
  },
  "guardian": {
    "name": "Guardian",
    "address": "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3",
    "chain_id": 84532,
    "explorer_url": "https://sepolia.basescan.org/address/0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"
  },
  "vault": {
    "name": "DemoVault",
    "address": "0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13",
    "chain_id": 84532,
    "explorer_url": "https://sepolia.basescan.org/address/0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13"
  },
  "chain_id": 84532,
  "sha256_state_fingerprint": "6758056f3f2c39400958a6a342258bf4308ec3d4f081f2b5d33068654d9507dd",
  "agent_summary": "Incident inc_6a2d... detected at 2026-09-05T19:22:25.984507+00:00. Vault 0xF1683d32... on Base Sepolia (chain 84532) was automatically paused via Guardian 0x8B7B1Ee7... Status: paused and verified on-chain. Pause tx: https://sepolia.basescan.org/tx/0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75 SHA-256 evidence fingerprint: 6758056f3f2c3940..."
}
```

---

## 2. Bazantic Model Context Protocol (MCP) Tools

The Bazantic MCP Server (`sentinel/bazantic/mcp_server.py`) allows Claude, GPT-4, and autonomous agents to investigate incidents via standard stdio JSON-RPC.

### Tool 1: `get_latest_incident`
- **Description:** Retrieve latest Sentinel circuit breaker incident record.
- **Parameters:**
  ```json
  {
    "type": "object",
    "properties": {
      "payment_proof": {
        "type": "string",
        "description": "Optional x402 payment proof token."
      }
    }
  }
  ```

### Tool 2: `verify_incident_evidence`
- **Description:** Cryptographically verify the SHA-256 state fingerprint of an incident response.
- **Parameters:**
  ```json
  {
    "type": "object",
    "required": ["incident_id", "sha256_fingerprint"],
    "properties": {
      "incident_id": {"type": "string"},
      "sha256_fingerprint": {"type": "string"}
    }
  }
  ```
- **Returns:** `{"valid": true, "match": true, "fingerprint": "6758056f..."}`.

---

## 3. Ledger ERC-7730 Clear Signing Specification

Defined in `sentinel/ledger/erc7730_unpause.json`, conforming to the official ERC-7730 v1 JSON schema:

```json
{
  "$schema": "https://erc7730.org/schema/v1/erc7730.schema.json",
  "context": {
    "$id": "nexguard-sentinel-guardian-unpause",
    "contract": {
      "deployments": [{"chainId": 84532, "address": "0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3"}]
    }
  },
  "display": {
    "formats": {
      "unpause(bytes32)": {
        "intent": "Unpause the NexGuard Vault circuit-breaker",
        "fields": [{"path": "reason", "label": "Unpause reason (keccak256)", "format": "bytes32"}]
      }
    }
  }
}
```
