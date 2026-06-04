from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository.core.interface import ItemT, KeyFn, RepositoryBase

from .store import KeyValueStore


@dataclass
class MultiKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]

    keys: list[KeyFn[ItemT]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.keys.insert(0, AttributeKey("id"))

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
