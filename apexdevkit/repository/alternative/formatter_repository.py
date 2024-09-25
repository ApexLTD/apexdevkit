from dataclasses import dataclass
from typing import Any, Generic, Iterator, Self

from apexdevkit.formatter import Formatter
from apexdevkit.repository.alternative import MemoryPersistence
from apexdevkit.repository.interface import ItemT

_Raw = dict[str, Any]


@dataclass
class FormatterRepository(Generic[ItemT]):
    base: MemoryPersistence
    formatter: Formatter[_Raw, ItemT]

    def create(self, item: ItemT) -> ItemT:
        return self.formatter.load(self.base.create(self.formatter.dump(item)))

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        return [
            self.formatter.load(
                self.base.create(
                    self.formatter.dump(item),
                ),
            )
            for item in items
        ]

    def read(self, item_id: str) -> ItemT:
        return self.formatter.load(self.base.read(item_id))

    def update(self, item: ItemT) -> None:
        self.base.update(self.formatter.dump(item))

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.base.update(self.formatter.dump(item))

    def delete(self, item_id: str) -> None:
        self.base.delete(item_id)

    def bind(self, **kwargs: Any) -> Self:
        return self

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.base:
            yield self.formatter.load(raw)

    def __len__(self) -> int:
        return len(self.base)
