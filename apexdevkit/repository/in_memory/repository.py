from __future__ import annotations

from collections.abc import Iterator
from contextlib import suppress
from dataclasses import dataclass, field

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository.core import ContainsMixin, ItemT, KeyFn, Repository

from .store import InMemoryByteStore, KeyValueStore


@dataclass(frozen=True)
class InMemoryRepository(ContainsMixin[ItemT], Repository[ItemT]):
    store: KeyValueStore[ItemT] = field(default_factory=InMemoryByteStore)
    keys: list[KeyFn[ItemT]] = field(default_factory=lambda: [AttributeKey("id")])

    def and_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        return self.with_key(function)

    def with_key(self, function: KeyFn[ItemT]) -> InMemoryRepository[ItemT]:
        self.keys.append(function)

        return self

    def and_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return self.with_seeded(*items)

    def with_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        for seed in items:
            with suppress(ExistsError):
                self.create(seed)

        return self

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
