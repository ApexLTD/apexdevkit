from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.core.interface import ItemT, KeyFn, RepositoryBase

from .store import KeyValueStore


@dataclass
class MultiKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]

    keys: list[KeyFn[ItemT]] = field(default_factory=list)

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self._pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            for key in self.keys:
                if key(new) == key(existing):
                    ExistsError(existing).with_duplicate(key).fire()

    def _pk(self, item: ItemT) -> str:
        return self.keys[0](item)

    def update(self, item: ItemT) -> None:
        self.delete(self._pk(item))
        self.create(item)

    def delete(self, item_id: str) -> None:
        item = self.read(item_id)
        self.store.drop(self._pk(item))

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
