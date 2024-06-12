from typing import Iterator

from apexdevkit.repository.interface import IdT, ItemT, Repository


class RepositoryBase(Repository[IdT, ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        raise NotImplementedError

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        raise NotImplementedError

    def read(self, item_id: IdT) -> ItemT:
        raise NotImplementedError

    def update(self, item: ItemT) -> None:
        raise NotImplementedError

    def update_many(self, items: list[ItemT]) -> None:
        raise NotImplementedError

    def delete(self, item_id: IdT) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[ItemT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
