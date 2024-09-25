from dataclasses import dataclass, field
from typing import Any, Iterator

from apexdevkit.error import DoesNotExistError, ExistsError

_Raw = dict[str, Any]


@dataclass
class MemoryRepositoryBase:  # pragma: no cover
    items: dict[str, _Raw] = field(init=False, default_factory=dict)

    def create(self, item: _Raw) -> _Raw:
        self._ensure_does_not_exist(item)
        self.items[item["id"]] = item

        return item

    def _ensure_does_not_exist(self, new: _Raw) -> None:
        if new["id"] in self.items.keys():
            error = ExistsError(self.items[new["id"]])
            error.with_duplicate(lambda item: f"id<{item['id']}>")
            error.fire()

    def create_many(self, items: list[_Raw]) -> list[_Raw]:
        for item in items:
            self.create(item)

        return items

    def read(self, item_id: str) -> _Raw:
        self._ensure_exists(item_id)

        return self.items[item_id]

    def _ensure_exists(self, item_id: str) -> None:
        if item_id not in self.items.keys():
            raise DoesNotExistError(item_id)

    def update(self, item: _Raw) -> None:
        self._ensure_exists(item["id"])

        self.delete(item["id"])
        self.create(item)

    def update_many(self, items: list[_Raw]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: str) -> None:
        self._ensure_exists(item_id)

        self.items.pop(item_id)

    def __iter__(self) -> Iterator[_Raw]:
        yield from self.items.values()

    def __len__(self) -> int:
        return len(self.items)
