"""Review metadata and consistency helpers; operator labels are not identities."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

CHAIN_ID = 84532
VAULT = "0xf1683d32fef59bbb95483561aba62a1bda65cd13"
GUARDIAN = "0x8b7b1ee7e335fd00f35cc6272c113c8735cb8ed3"
DEPLOYMENT = "QmNcPyyo2Ybz1M3Lmg1eAE8A6ATuhZ3RvqePiks18fTfcQ"
UNIT = "DemoVault accounting units (valueless)"
Disposition = Literal["policy_breach", "expected_activity", "insufficient_evidence"]


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["acknowledge", "resolve"]
    revision: int = Field(ge=0)
    request_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    operator: str = Field(min_length=1, max_length=80)
    note: str = Field(min_length=1, max_length=2000)
    disposition: Disposition | None = None

    @model_validator(mode="after")
    def validate_transition(self) -> Self:
        self.operator, self.note = self.operator.strip(), self.note.strip()
        if not self.operator or not self.note:
            raise ValueError("Operator label and note cannot be blank")
        if (self.action == "resolve") != (self.disposition is not None):
            raise ValueError("Only resolution requires a disposition")
        return self
