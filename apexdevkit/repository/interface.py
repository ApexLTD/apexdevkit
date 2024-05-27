from typing import Iterator, Protocol, TypeVar

ItemT = TypeVar("ItemT")
IdT = TypeVar("IdT", contravariant=True)


class Repository(Protocol[IdT, ItemT]):
    def create(self, item: ItemT) -> None:
        pass

    def create_many(self, items: list[ItemT]) -> None:
        pass

    def read(self, item_id: IdT) -> ItemT:
        pass

    def update(self, item: ItemT) -> None:
        pass

    def update_many(self, items: list[ItemT]) -> None:
        pass

    def delete(self, item_id: IdT) -> None:
        pass

    def __iter__(self) -> Iterator[ItemT]:
        pass

    def __len__(self) -> int:
        pass
