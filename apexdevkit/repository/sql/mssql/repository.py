from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from pymssql import DatabaseError, OperationalError

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository import Database, Repository
from apexdevkit.repository.core import ContainsMixin, ItemT
from apexdevkit.repository.sql.connector import MsSqlConnector
from apexdevkit.repository.sql.mssql.table import SqlTable


@dataclass(frozen=True, kw_only=True)
class MsSqlRepository(ContainsMixin, Repository[ItemT]):
    table: SqlTable[ItemT]

    db: Database = field(default_factory=lambda: Database(connector=MsSqlConnector()))

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.db.execute(self.table.select_all()).fetch_all():
            yield self.table.load(raw)

    def __len__(self) -> int:
        raw = self.db.execute(self.table.count_all()).fetch_one()

        try:
            return int(raw["n_items"])
        except KeyError as e:
            raise UnknownError(raw) from e

    def delete(self, item_id: str) -> None:
        self.db.execute(self.table.delete(item_id)).fetch_none()

    def delete_all(self) -> None:
        self.db.execute(self.table.delete_all()).fetch_none()

    def create(self, item: ItemT) -> ItemT:
        try:
            return self.table.load(self.db.execute(self.table.insert(item)).fetch_one())
        except DatabaseError as e:
            if MssqlException(e).is_duplication():
                raise self.table.exists(item) from e

            raise UnknownError(MssqlException(e).message) from e

    def read(self, item_id: str) -> ItemT:
        try:
            raw = self.db.execute(self.table.select(item_id)).fetch_one()
        except OperationalError as e:
            if "Conversion failed" in str(e):
                raise DoesNotExistError(item_id) from e
            raise e

        if not raw:
            raise DoesNotExistError(item_id)

        return self.table.load(raw)

    def update(self, item: ItemT) -> None:
        self.db.execute(self.table.update(item)).fetch_none()


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
