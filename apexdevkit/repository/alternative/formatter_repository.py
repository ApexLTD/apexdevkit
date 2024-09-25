from dataclasses import dataclass
from typing import Any, Generic, Iterator

from apexdevkit.formatter import Formatter
from apexdevkit.repository.alternative import MemoryRepositoryBase
from apexdevkit.repository.alternative.interface import ItemT

_Raw = dict[str, Any]


@dataclass
class FormatterRepository(Generic[ItemT]):
    base: MemoryRepositoryBase
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
        [self.base.update(self.formatter.dump(item)) for item in items]

    def delete(self, item_id: str) -> None:
        self.base.delete(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.base:
            yield self.formatter.load(raw)

    def __len__(self) -> int:
        return len(self.base)
