from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import IntegrityError
from typing import Any, Generic, Iterator, TypeVar

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import Database, DatabaseCommand

ItemT = TypeVar("ItemT")


@dataclass
class SqliteRepository(Generic[ItemT]):
    db: Database
    table: SqlTable[ItemT]

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.db.execute(self.table.select_all()).fetch_all():
            yield self.table.load(raw)

    def __len__(self) -> int:
        raw = self.db.execute(self.table.count_all()).fetch_one()

        try:
            return int(raw["n_items"])
        except KeyError:
            raise UnknownError(raw)

    def create(self, item: ItemT) -> ItemT:
        try:
            return self.table.load(self.db.execute(self.table.insert(item)).fetch_one())
        except IntegrityError:  # pragma: no cover
            item = self.table.load(
                self.db.execute(self.table.select_duplicate(item)).fetch_one()
            )
            self.table.duplicate(item).fire()
            return item

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        return [self.create(item) for item in items]

    def read(self, item_id: str) -> ItemT:
        raw = self.db.execute(self.table.select(item_id)).fetch_one()

        if not raw:
            raise DoesNotExistError(item_id)

        return self.table.load(raw)

    def update(self, item: ItemT) -> None:
        self.db.execute(self.table.update(item)).fetch_none()

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: str) -> None:
        self.db.execute(self.table.delete(item_id)).fetch_none()

    def delete_all(self) -> None:
        self.db.execute(self.table.delete_all()).fetch_none()


class SqlTable(Generic[ItemT]):  # pragma: no cover
    def count_all(self) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def insert(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def select(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def select_duplicate(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def select_all(self) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def update(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def delete(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def delete_all(self) -> DatabaseCommand:
        raise NotImplementedError("Not implemented")

    def load(self, data: dict[str, Any]) -> ItemT:
        raise NotImplementedError("Not implemented")

    def duplicate(self, item: ItemT) -> ExistsError:
        return ExistsError(item).with_duplicate(lambda i: "Unknown")


@dataclass
class UnknownError(Exception):
    raw: dict[str, Any]
