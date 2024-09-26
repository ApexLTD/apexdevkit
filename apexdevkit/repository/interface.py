from __future__ import annotations

from typing import Any, Iterator, Protocol, TypeVar

ItemT = TypeVar("ItemT")


class Repository(Protocol[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        pass

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        pass

    def read(self, item_id: str) -> ItemT:
        pass

    def update(self, item: ItemT) -> None:
        pass

    def update_many(self, items: list[ItemT]) -> None:
        pass

    def delete(self, item_id: str) -> None:
        pass

    def bind(self, **kwargs: Any) -> Repository[ItemT]:
        pass

    def __iter__(self) -> Iterator[ItemT]:
        pass

    def __len__(self) -> int:
        pass
