from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, Protocol, TypeVar

ItemT = TypeVar("ItemT")


class Repository(Protocol[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        pass

    def read(self, item_id: str) -> ItemT:
        pass

    def update(self, item: ItemT) -> None:
        pass

    def delete(self, item_id: str) -> None:
        pass

    def __iter__(self) -> Iterator[ItemT]:
        pass

    def __len__(self) -> int:
        pass


class BatchRepository(Repository[ItemT], Protocol[ItemT]):  # pragma: no cover
    def create_many(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        pass

    def update_many(self, items: Iterable[ItemT]) -> None:
        pass


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
