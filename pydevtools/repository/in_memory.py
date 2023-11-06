from dataclasses import dataclass, field
from typing import Any, Generic, Iterator, Protocol, TypeVar

from pydevtools.error import DoesNotExistError, ExistsError


class _Item(Protocol):
    id: Any


ItemT = TypeVar("ItemT", bound=_Item)


@dataclass
class InMemoryRepository(Generic[ItemT]):
    items: dict[str, ItemT] = field(default_factory=dict)

    def create(self, item: ItemT) -> None:
        self._ensure_does_not_exist(item)
        self.items[str(item.id)] = item

    def _ensure_does_not_exist(self, item: ItemT) -> None:
        for existing in self.items.values():
            if item == existing:
                raise ExistsError(existing.id)

    def read(self, item_id: Any) -> ItemT:
        try:
            return self.items[str(item_id)]
        except KeyError:
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
