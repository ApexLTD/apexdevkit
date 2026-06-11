from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Protocol


class Authority(Protocol):
    def sign(self, message: str) -> Signature:
        pass

    def verify(self, message: str, signature: Signature) -> bool:
        pass


@dataclass(frozen=True, kw_only=True)
class Signature:
    name: str
    value: str


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
