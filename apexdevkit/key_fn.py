from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return str(getattr(item, self.name))
