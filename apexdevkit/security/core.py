from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Authority(Protocol):  # pragma: no cover
    def sign(self, message: str) -> Signature:
        pass

    def verify(self, message: str, signature: Signature) -> bool:
        pass


@dataclass(frozen=True, kw_only=True)
class Signature:
    name: str
    value: str
