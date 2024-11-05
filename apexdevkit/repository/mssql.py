from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Iterator, TypeVar

from pymssql.exceptions import DatabaseError

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import Database, DatabaseCommand, RepositoryBase

ItemT = TypeVar("ItemT")


@dataclass
class MsSqlRepository(RepositoryBase[ItemT]):
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

    def delete(self, item_id: str) -> None:
        self.db.execute(self.table.delete(item_id)).fetch_none()

    def delete_all(self) -> None:
        self.db.execute(self.table.delete_all()).fetch_none()

    def create(self, item: ItemT) -> ItemT:
        try:
            return self.table.load(self.db.execute(self.table.insert(item)).fetch_one())
        except DatabaseError as e:
            e = MssqlException(e)

            if e.is_duplication():
                raise self.table.exists(item)

            raise UnknownError(e.message)

    def read(self, item_id: str) -> ItemT:
        raw = self.db.execute(self.table.select(item_id)).fetch_one()

        if not raw:
            raise DoesNotExistError(item_id)

        return self.table.load(raw)

    def update(self, item: ItemT) -> None:
        self.db.execute(self.table.update(item)).fetch_none()


class SqlTable(Generic[ItemT]):  # pragma: no cover
    def count_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def insert(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError

    def select(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def select_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def delete(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def delete_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def update(self, item: ItemT) -> DatabaseCommand:
        raise NotImplementedError

    def load(self, data: dict[str, Any]) -> ItemT:
        raise NotImplementedError

    def exists(self, duplicate: ItemT) -> ExistsError:
        raise NotImplementedError


@dataclass
class MssqlException:
    code: int
    message: str

    def __init__(self, e: DatabaseError):
        self.code = e.args[0]
        self.message = e.args[1].decode()

    def is_duplication(self) -> bool:
        return self.code in [2627, 70003]


@dataclass
class UnknownError(Exception):
    raw: Any
