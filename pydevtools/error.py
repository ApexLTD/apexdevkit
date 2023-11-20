from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self


@dataclass
class ExistsError(Exception):
    id: Any

    _duplicates: dict[str, Any] = field(init=False, default_factory=dict)

    def with_duplicate(self, **fields: Any) -> Self:
        for key, value in fields.items():
            self._duplicates[key] = value

        return self

    def __str__(self) -> str:
        return ",".join([f"{k}<{v}>" for k, v in self._duplicates.items()])

    def fire(self) -> None:
        if self._duplicates:
            raise self


@dataclass
class DoesNotExistError(Exception):
    id: Any
