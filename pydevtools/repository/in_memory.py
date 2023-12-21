from dataclasses import dataclass, field
from typing import Any, Generic, Iterator, Protocol, Self, TypeVar

from pydevtools.error import DoesNotExistError, ExistsError


class _Item(Protocol):
    id: Any


ItemT = TypeVar("ItemT", bound=_Item)


@dataclass
class InMemoryRepository(Generic[ItemT]):
    items: dict[str, ItemT] = field(default_factory=dict)

    uniques: list[str] = field(default_factory=list)
    search_by: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.search_by = ["id", *self.search_by]

    def with_unique(self, attribute: str) -> Self:
        self.uniques.append(attribute)

        return self

    def with_searchable(self, attribute: str) -> Self:
        self.search_by.append(attribute)

        return self

    def create_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.create(item)

    def create(self, item: ItemT) -> None:
        self._ensure_does_not_exist(item)
        self.items[str(item.id)] = item

    def _ensure_does_not_exist(self, item: ItemT) -> None:
        for existing in self.items.values():
            error = ExistsError(existing.id)
            for name in self.uniques:
                if getattr(item, name) == getattr(existing, name):
                    error.with_duplicate(**{name: getattr(item, name)})

            error.fire()

        assert str(item.id) not in self.items, f"Item with id<{item.id}> already exists"

    def read(self, item_id: Any) -> ItemT:
        for item in self.items.values():
            for attribute in self.search_by:
                if getattr(item, attribute) == item_id:
                    return item

        raise DoesNotExistError(item_id)

    def update(self, item: ItemT) -> None:
        self.delete(item.id)
        self.create(item)

    def delete(self, item_id: Any) -> None:
        del self.items[str(item_id)]

    def __iter__(self) -> Iterator[ItemT]:
        yield from self.items.values()

    def __len__(self) -> int:
        return len(self.items)
