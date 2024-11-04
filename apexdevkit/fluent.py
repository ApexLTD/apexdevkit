from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

ItemT = TypeVar("ItemT")


class FluentDict(dict[str, ItemT]):
    def value_of(self, key: str) -> FluentElement[ItemT]:
        return FluentElement(self[key])

    def and_a(self, **fields: ItemT) -> FluentDict[ItemT]:
        return self.with_a(**fields)

    def with_a(self, **fields: ItemT) -> FluentDict[ItemT]:
        return self.merge(FluentDict[ItemT](fields))

    def merge(self, other: FluentDict[ItemT]) -> FluentDict[ItemT]:
        return FluentDict[ItemT]({**self, **other})

    def drop(self, *keys: str) -> FluentDict[ItemT]:
        return self.select(*set(self.keys()).difference(keys))

    def select(self, *keys: str) -> FluentDict[ItemT]:
        return FluentDict[ItemT]({k: v for k, v in self.items() if k in keys})


@dataclass(frozen=True)
class FluentElement(Generic[ItemT]):
    value: ItemT

    def to(self, a_type: Callable[[ItemT], ConvertedT]) -> ConvertedT:
        return a_type(self.value)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.value)  # type: ignore

    def __str__(self) -> str:
        return str(self.value)


ConvertedT = TypeVar("ConvertedT")
