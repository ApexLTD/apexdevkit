from __future__ import annotations

import hmac
from dataclasses import dataclass


@dataclass(frozen=True)
class Hmac:
    secret: str

    algorithm: str = "sha256"

    def __call__(self, value: str) -> bytes:
        return self.hash(value)

    def hash(self, value: str) -> bytes:
        return hmac.new(
            key=self.secret.encode("utf-8"),
            msg=value.encode("utf-8"),
            digestmod=self.algorithm,
        ).digest()
