from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Generic, Protocol

from apexdevkit.formatter import Formatter, PickleFormatter
from apexdevkit.repository.core.interface import ItemT


class KeyValueStore(Protocol[ItemT]):  # pragma: no cover
    def count(self) -> int:
        pass

    def set(self, key: str, value: ItemT) -> None:
        pass

    def get(self, key: str) -> ItemT:
        pass

    def drop(self, key: str) -> None:
        pass

    def values(self) -> Iterable[ItemT]:
        pass


@dataclass
class InMemoryByteStore(Generic[ItemT]):
    formatter: Formatter[bytes, ItemT] = field(default_factory=PickleFormatter)

    items: dict[str, bytes] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.items)

    def set(self, key: str, value: ItemT) -> None:
        self.items[key] = self.formatter.dump(value)

    def get(self, key: str) -> ItemT:
        return self.formatter.load(self.items[key])

    def drop(self, key: str) -> None:
        del self.items[key]

    def values(self) -> Iterable[ItemT]:
        for raw in self.items.values():
            yield self.formatter.load(raw)
