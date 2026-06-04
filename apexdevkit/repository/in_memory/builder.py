from __future__ import annotations

from collections.abc import Iterator
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository import Entity
from apexdevkit.repository.core import ItemT, Repository, RepositoryBase
from apexdevkit.repository.core.interface import KeyFn

from .store import KeyValueStore

_T = TypeVar("_T", bound=Entity)


@dataclass(frozen=True)
class InMemoryRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]

    keys: list[KeyFn[ItemT]] = field(default_factory=lambda: [AttributeKey("id")])

    def add_key(self, key: KeyFn[ItemT]) -> None:
        self.keys.append(key)

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(item.id, item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            for key in self.keys:
                if key(new) == key(existing):
                    ExistsError(existing).with_duplicate(key).fire()

    def update(self, item: ItemT) -> None:
        self.delete(item.id)
        self.create(item)

    def delete(self, item_id: str) -> None:
        item = self.read(item_id)
        self.store.drop(item.id)

    def read(self, item_id: str) -> ItemT:
        for key in self.keys:
            for item in self:
                if key(item) == str(item_id):
                    return item

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()

    @dataclass(frozen=True)
    class Builder(Generic[_T]):
        repository: InMemoryRepository[_T]

        def and_key(self, function: KeyFn[_T]) -> InMemoryRepository.Builder[_T]:
            return self.with_key(function)

        def with_key(self, function: KeyFn[_T]) -> InMemoryRepository.Builder[_T]:
            self.repository.add_key(function)

            return self

        def and_seeded(self, *items: _T) -> InMemoryRepository.Builder[_T]:
            return self.with_seeded(*items)

        def with_seeded(self, *items: _T) -> InMemoryRepository.Builder[_T]:
            for seed in items:
                with suppress(ExistsError):
                    self.repository.create(seed)

            return self

        def build(self) -> Repository[_T]:
            return self.repository

    @classmethod
    def with_store(
        cls, value: KeyValueStore[ItemT]
    ) -> InMemoryRepository.Builder[ItemT]:
        return InMemoryRepository.Builder(InMemoryRepository(value))
