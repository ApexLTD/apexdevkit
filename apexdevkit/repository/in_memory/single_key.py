from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.core.interface import ItemT, KeyFn, RepositoryBase

from .store import KeyValueStore


@dataclass
class SingleKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]
    pk: KeyFn[ItemT]

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self.pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        try:
            existing = self.store.get(self.pk(new))
        except KeyError:
            return

        ExistsError(existing).with_duplicate(self.pk).fire()

    def update(self, item: ItemT) -> None:
        self.delete(self.pk(item))
        self.create(item)

    def delete(self, item_id: str) -> None:
        try:
            self.store.drop(item_id)
        except KeyError as e:
            raise DoesNotExistError(item_id) from e

    def read(self, item_id: str) -> ItemT:
        try:
            return self.store.get(item_id)
        except KeyError as e:
            raise DoesNotExistError(item_id) from e

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()
