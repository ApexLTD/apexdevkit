from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from typing import Generic

from apexdevkit.error import ExistsError
from apexdevkit.repository.core.interface import ItemT, KeyFn, Repository

from .multi_key import MultiKeyRepository
from .single_key import SingleKeyRepository
from .store import InMemoryByteStore, KeyValueStore


@dataclass(frozen=True)
class InMemoryRepository(Generic[ItemT]):
    store: KeyValueStore[ItemT] = field(default_factory=lambda: InMemoryByteStore())
    keys: list[KeyFn[ItemT]] = field(default_factory=list)
    seeds: frozenset[ItemT] = field(default_factory=frozenset)

    def with_store(self, value: KeyValueStore[ItemT]) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(store=value, keys=self.keys, seeds=self.seeds)

    def and_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        return self.with_key(function)

    def with_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(
            store=self.store,
            keys=[*self.keys, function],
            seeds=self.seeds,
        )

    def and_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return self.with_seeded(*items)

    def with_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(
            store=self.store,
            keys=self.keys,
            seeds=self.seeds.union(set(items)),
        )

    def build(self) -> Repository[ItemT]:
        return self._seed(self._create())

    def _seed(self, repository: Repository[ItemT]) -> Repository[ItemT]:
        for seed in self.seeds:
            with suppress(ExistsError):
                repository.create(seed)

        return repository

    def _create(self) -> Repository[ItemT]:
        if len(self.keys) == 0:
            return SingleKeyRepository(self.store)

        return MultiKeyRepository(self.store, keys=self.keys)
