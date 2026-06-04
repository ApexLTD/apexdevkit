from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import Generic

from apexdevkit.error import ExistsError
from apexdevkit.repository.core.interface import ItemT, KeyFn, Repository

from .multi_key import MultiKeyRepository
from .store import KeyValueStore


@dataclass(frozen=True)
class InMemoryRepository(Generic[ItemT]):
    repository: MultiKeyRepository[ItemT]

    @classmethod
    def with_store(cls, value: KeyValueStore[ItemT]) -> InMemoryRepository[ItemT]:
        return cls(MultiKeyRepository(store=value))

    def and_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        return self.with_key(function)

    def with_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        self.repository.add_key(function)

        return self

    def and_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return self.with_seeded(*items)

    def with_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        for seed in items:
            with suppress(ExistsError):
                self.repository.create(seed)

        return self

    def build(self) -> Repository[ItemT]:
        return self.repository
