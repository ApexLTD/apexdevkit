from collections.abc import Iterator
from typing import Generic

from apexdevkit.repository.interface import ItemT


class RepositoryBase(Generic[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        raise NotImplementedError

    def read(self, item_id: str) -> ItemT:
        raise NotImplementedError

    def update(self, item: ItemT) -> None:
        raise NotImplementedError

    def delete(self, item_id: str) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[ItemT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
