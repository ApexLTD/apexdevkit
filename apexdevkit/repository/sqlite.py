from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import IntegrityError
from typing import Any, Generic, Iterator

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import Database, DatabaseCommand, RepositoryBase
from apexdevkit.repository.interface import ItemT


@dataclass(frozen=True)
class SqliteRepository(RepositoryBase[ItemT]):
    db: Database
    table: SqlTable[ItemT]

    def bind(self, **kwargs: Any) -> SqliteRepository[ItemT]:
        return SqliteRepository(self.db, self.table.bind(**kwargs))

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

    def read(self, item_id: str) -> ItemT:
        raw = self.db.execute(self.table.select(str(item_id))).fetch_one()

        if not raw:
            raise DoesNotExistError(item_id)

        return self.table.load(raw)

    def update(self, item: ItemT) -> None:
        self.db.execute(self.table.update(item)).fetch_none()

    def delete(self, item_id: str) -> None:
        self.db.execute(self.table.delete(str(item_id))).fetch_none()

    def delete_all(self) -> None:
        self.db.execute(self.table.delete_all()).fetch_none()


class SqlTable(Generic[ItemT]):  # pragma: no cover
    def bind(self, **kwargs: Any) -> SqlTable[ItemT]:
        return self

    def count_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def insert(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError

    def select(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def select_duplicate(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError

    def select_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def update(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError

    def delete(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def delete_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def load(self, data: dict[str, Any]) -> ItemT:
        raise NotImplementedError

    def duplicate(self, item: ItemT) -> ExistsError:
        return ExistsError(item).with_duplicate(lambda i: "Unknown")


@dataclass
class UnknownError(Exception):
    raw: dict[str, Any]
