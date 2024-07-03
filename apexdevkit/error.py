from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Self

Criteria = Callable[[Any], str]


class UnknownItem:
    @property
    def id(self) -> str:
        return "unknown"


@dataclass
class ExistsError(Exception):
    item: Any = field(default_factory=UnknownItem)

    _duplicates: list[Criteria] = field(init=False, default_factory=list)

    @property
    def id(self) -> Any:
        return self.item.id

    def with_duplicate(self, criteria: Criteria) -> Self:
        self._duplicates.append(criteria)

        return self

    def __str__(self) -> str:
        return ",".join([f"{criteria(self.item)}" for criteria in self._duplicates])

    def fire(self) -> None:
        if self._duplicates:
            raise self


@dataclass
class DoesNotExistError(Exception):
    id: Any = "unknown"


@dataclass
class ForbiddenError(Exception):
    item: Any = field(default_factory=UnknownItem)
    message: str = "Forbidden"

    @property
    def id(self) -> Any:
        return self.item.id


@dataclass
class ApiError(Exception):
    code: int
    data: dict[str, Any]
