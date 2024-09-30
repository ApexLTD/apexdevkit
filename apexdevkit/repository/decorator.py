from dataclasses import dataclass
from typing import Any, Iterable, Iterator

from apexdevkit.repository.base import RepositoryBase
from apexdevkit.repository.interface import ItemT, Repository


@dataclass
class RepositoryDecorator(RepositoryBase[ItemT]):
    inner: Repository[ItemT]

    def create(self, item: ItemT) -> ItemT:
        return self.inner.create(item)

    def read(self, item_id: str) -> ItemT:
        return self.inner.read(item_id)

    def update(self, item: ItemT) -> None:
        self.inner.update(item)

    def delete(self, item_id: str) -> None:
        self.inner.delete(item_id)

    def bind(self, **kwargs: Any) -> Repository[ItemT]:
        return self.inner.bind(**kwargs)

    def __iter__(self) -> Iterator[ItemT]:
        return self.inner.__iter__()

    def __len__(self) -> int:
        return self.inner.__len__()


class BatchRepositoryDecorator(RepositoryDecorator[ItemT]):
    def create_many(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        return [self.inner.create(item) for item in items]

    def update_many(self, items: Iterable[ItemT]) -> None:
        for item in items:
            self.inner.update(item)
