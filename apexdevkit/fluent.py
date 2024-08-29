from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

ItemT = TypeVar("ItemT")


class FluentDict(dict[str, ItemT]):
    def value_of(self, key: str) -> FluentElement:
        return FluentElement(self[key])

    def and_a(self, **fields: ItemT) -> FluentDict:
        return self.with_a(**fields)

    def with_a(self, **fields: ItemT) -> FluentDict:
        return self.merge(FluentDict(fields))

    def merge(self, other: FluentDict) -> FluentDict:
        return FluentDict({**self, **other})

    def drop(self, *keys: str) -> FluentDict:
        return self.select(*set(self.keys()).difference(keys))

    def select(self, *keys: str) -> FluentDict:
        return FluentDict({k: v for k, v in self.items() if k in keys})


@dataclass
class FluentElement(Generic[ItemT]):
    value: ItemT

    def to(self, a_type: Callable[[ItemT], ConvertedT]) -> ConvertedT:
        return a_type(self.value)

    def __str__(self) -> str:
        return str(self.value)


ConvertedT = TypeVar("ConvertedT")
