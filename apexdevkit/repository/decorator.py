from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

from apexdevkit.repository import Repository

ItemT = TypeVar("ItemT")
IdT = TypeVar("IdT", contravariant=True)


@dataclass
class RepositoryDecorator(Generic[IdT, ItemT]):
    inner: Repository[IdT, ItemT]

    def create(self, item: ItemT) -> ItemT:
        return self.inner.create(item)

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        return self.inner.create_many(items)

    def read(self, item_id: IdT) -> ItemT:
        return self.inner.read(item_id)

    def update(self, item: ItemT) -> None:
        self.inner.update(item)

    def update_many(self, items: list[ItemT]) -> None:
        self.inner.update_many(items)

    def delete(self, item_id: IdT) -> None:
        self.inner.delete(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return self.inner.__iter__()

    def __len__(self) -> int:
        return self.inner.__len__()
