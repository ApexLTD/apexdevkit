from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterator, Protocol, TypeVar

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.database import MongoDatabase


class _Item(Protocol):  # pragma: no cover
    @property
    def id(self) -> Any:
        pass


ItemT = TypeVar("ItemT", bound=_Item)


@dataclass
class MongoDBRepository(Generic[ItemT]):
    database: MongoDatabase
    table: MongoTable[ItemT]

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.database:
            yield self.table.load(raw)

    def __len__(self) -> int:
        return len(self.database)

    def create(self, item: ItemT) -> ItemT:
        try:
            self.read(item.id)
            raise ExistsError(item).with_duplicate(
                lambda i: f"_Item with id<{i.id}> already exists."
            )
        except DoesNotExistError:
            self.database.create(self.table.to_dict(item))
            return item

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        return [self.create(item) for item in items]

    def read(self, item_id: str) -> ItemT:
        raw = self.database.read(item_id)

        if not raw:
            raise DoesNotExistError(item_id)

        return self.table.load(raw)

    def update(self, item: ItemT) -> None:
        self.database.update(
            self.table.get_id(item),
            self.table.to_dict(item),
        )

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: str) -> None:
        result = self.database.delete(item_id)
        if result.deleted_count == 0:
            raise DoesNotExistError(item_id)

    def delete_all(self) -> None:
        self.database.delete_all()


class MongoTable(Generic[ItemT]):
    def to_dict(self, item: ItemT) -> Dict[str, Any]:
        raise NotImplementedError("Not implemented")

    def load(self, data: Dict[str, Any]) -> ItemT:
        raise NotImplementedError("Not implemented")

    def get_id(self, item: ItemT) -> str:
        raise NotImplementedError("Not implemented")
