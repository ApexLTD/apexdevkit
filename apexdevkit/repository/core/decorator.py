from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from .interface import ItemT, Repository


@dataclass
class RepositoryDecorator(Repository[ItemT]):  # pragma: no cover
    inner: Repository[ItemT]

    def create(self, item: ItemT) -> ItemT:
        return self.inner.create(item)

    def read(self, item_id: str) -> ItemT:
        return self.inner.read(item_id)

    def update(self, item: ItemT) -> None:
        self.inner.update(item)

    def delete(self, item_id: str) -> None:
        self.inner.delete(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.inner)

    def __len__(self) -> int:
        return len(self.inner)

    def __contains__(self, item: object) -> bool:
        return item in self.inner


class BruteForceBatch(RepositoryDecorator[ItemT]):
    def create_many(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        return [self.inner.create(item) for item in items]

    def update_many(self, items: Iterable[ItemT]) -> None:
        for item in items:
            self.inner.update(item)
