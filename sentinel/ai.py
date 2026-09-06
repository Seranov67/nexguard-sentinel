"""Bounded Ollama structured-output client; no wallet or signer capability."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

PROMPT_VERSION = "sentinel-classifier-v1"
SYSTEM_PROMPT = (
    "Classify numeric withdrawal features from a valueless testnet vault. "
    "Return only the requested JSON schema. Critical pause is appropriate for "
    "a total amount at least 10000000000000000000 accounting units, or sustained "
    "high velocity (velocity_bps >= 25000 with event_count >= 3). Otherwise "
    "recommend notify for unusual activity or none for normal activity. "
    "Explain the numeric signal within 240 characters. You propose only; "
    "deterministic policy enforces transaction authorization."
)
PROMPT_HASH = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
        "recommended_action": {"type": "string", "enum": ["none", "notify", "pause"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 240},
    },
    "required": ["severity", "recommended_action", "confidence", "rationale"],
}


@dataclass(frozen=True)
class OllamaEvaluator:
    endpoint: str
    model: str
    timeout: float = 30

    def __post_init__(self) -> None:
        url = urlsplit(self.endpoint)
        local = url.hostname in ("127.0.0.1", "localhost", "::1")
        if url.username or url.query or url.fragment or not url.hostname:
            raise ValueError("Invalid AI endpoint")
        if url.scheme != "https" and not (local and url.scheme == "http"):
            raise ValueError("AI endpoint requires HTTPS or local HTTP")
        if not self.model.strip() or not 0 < self.timeout <= 60:
            raise ValueError("Model and bounded timeout required")

    def __call__(self, features: dict[str, Any]) -> str:
        encoded = json.dumps(features, sort_keys=True)
        if len(encoded) > 4096:
            raise ValueError("AI input exceeds limit")
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                self.endpoint.rstrip("/") + "/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "format": SCHEMA,
                    "options": {"temperature": 0, "num_predict": 256},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": encoded},
                    ],
                },
            ) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 32768:
                        raise ValueError("AI response exceeds limit")
        data = json.loads(body)
        if data.get("done") is not True:
            raise ValueError("Incomplete AI response")
        content = data["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("AI content is not text")
        return content
