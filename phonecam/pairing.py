from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class PairingToken:
    value: str

    @classmethod
    def create(cls) -> "PairingToken":
        return cls(secrets.token_urlsafe(32))

    def matches(self, candidate: str | None) -> bool:
        if candidate is None:
            return False
        return hmac.compare_digest(self.value, candidate)
