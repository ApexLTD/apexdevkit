from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

KeyFn = Callable[[Any], str]


@dataclass(frozen=True)
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return str(getattr(item, self.name))
