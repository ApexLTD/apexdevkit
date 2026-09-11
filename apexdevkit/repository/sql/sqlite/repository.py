from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from sqlite3 import IntegrityError
from typing import Any

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository import Database, Repository
from apexdevkit.repository.core import ContainsMixin, ItemT
from apexdevkit.repository.sql.connector import SqliteFileConnector
from apexdevkit.repository.sql.sqlite.table import SqlTable


@dataclass(frozen=True, kw_only=True)
class SqliteRepository(ContainsMixin, Repository[ItemT]):
    table: SqlTable[ItemT]

    db: Database = field(default_factory=lambda: Database(SqliteFileConnector()))

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.db.execute(self.table.select_all()).fetch_all():
            yield self.table.load(raw)

    def __len__(self) -> int:
        raw = self.db.execute(self.table.count_all()).fetch_one()

        try:
            return int(raw["n_items"])
        except KeyError as e:
            raise UnknownError(raw) from e

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


@dataclass
class UnknownError(Exception):
    raw: Mapping[str, Any]
