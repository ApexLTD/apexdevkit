from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import IntegrityError
from typing import Any, Generic, Iterable, Iterator

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
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


@dataclass(frozen=True)
class SqliteTableBuilder(Generic[ItemT]):
    table_name: str | None = None
    formatter: Formatter[dict[str, Any], ItemT] | None = None
    fields: list[SqliteField] | None = None

    def with_name(self, value: str) -> SqliteTableBuilder[ItemT]:
        return SqliteTableBuilder[ItemT](value, self.formatter, self.fields)

    def with_formatter(
        self, value: Formatter[dict[str, Any], ItemT]
    ) -> SqliteTableBuilder[ItemT]:
        return SqliteTableBuilder[ItemT](self.table_name, value, self.fields)

    def with_fields(self, fields: Iterable[str]) -> SqliteTableBuilder[ItemT]:
        return SqliteTableBuilder[ItemT](
            self.table_name,
            self.formatter,
            [SqliteField(field, field == "id", False) for field in list(fields)],
        )

    def with_id(self, identifier: str) -> SqliteTableBuilder[ItemT]:
        assert self.fields is not None, "Set fields first."
        if identifier not in [field.name for field in self.fields]:
            raise ValueError("Missing fields in the table.")

        return SqliteTableBuilder[ItemT](
            self.table_name,
            self.formatter,
            [
                SqliteField(field.name, field.name == identifier, field.is_composite)
                for field in self.fields
            ],
        )

    def with_composite_key(
        self, composites: Iterable[str]
    ) -> SqliteTableBuilder[ItemT]:
        assert self.fields is not None, "Set fields first."

        names = [field.name for field in self.fields]
        if not all(field in names for field in list(composites)):
            raise ValueError("Missing fields in the table.")

        return SqliteTableBuilder[ItemT](
            self.table_name,
            self.formatter,
            [
                SqliteField(field.name, field.is_id, field.name in list(composites))
                for field in self.fields
            ],
        )

    def build(self) -> SqlTable[ItemT]:
        if not self.table_name or not self.formatter or not self.fields:
            raise ValueError("Cannot build sql table.")

        return _DefaultSqlTable(self.table_name, self.formatter, self.fields)


@dataclass(frozen=True)
class _DefaultSqlTable(SqlTable[ItemT]):
    table_name: str
    formatter: Formatter[dict[str, Any], ItemT]
    fields: list[SqliteField]

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            SELECT count(*) as n_items
            FROM {self.table_name.capitalize()};
        """)

    def insert(self, item: ItemT) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])
        placeholders = ", ".join([f":{key.name}" for key in self.fields])

        return DatabaseCommand(f"""
            INSERT INTO {self.table_name.capitalize()} (
                {columns}
            ) VALUES (
                {placeholders}
            )
            RETURNING {columns};
        """).with_data(self.formatter.dump(item))

    def select(self, item_id: str) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns} 
            FROM {self.table_name.capitalize()}
            WHERE {self._id} = :{self._id};
        """).with_data({self._id: item_id})

    def select_duplicate(self, item: ItemT) -> DatabaseCommand:
        raw = self.formatter.dump(item)
        columns = ", ".join([field.name for field in self.fields])

        duplicates = " AND ".join([f"{field} = :{field}" for field in self._composite])

        return DatabaseCommand(f"""
            SELECT
                {columns} 
            FROM {self.table_name.capitalize()}
            WHERE {duplicates};
        """).with_data({key: raw[key] for key in raw if key in self._composite})

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns}
            FROM {self.table_name.capitalize()};
        """)

    def update(self, item: ItemT) -> DatabaseCommand:
        updates = ", ".join(
            [
                f"{field.name} = :{field.name}"
                for field in self.fields
                if not field.is_id
            ]
        )

        return DatabaseCommand(f"""
            UPDATE {self.table_name.capitalize()}
            SET
                {updates}
            WHERE
                {self._id} = :{self._id};
        """).with_data(self.formatter.dump(item))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.capitalize()}
            WHERE
                {self._id} = :{self._id};
        """).with_data({self._id: item_id})

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.capitalize()};
        """)

    def load(self, data: dict[str, Any]) -> ItemT:
        return self.formatter.load(data)

    def duplicate(self, item: ItemT) -> ExistsError:
        raw = self.formatter.dump(item)
        return ExistsError(item).with_duplicate(
            lambda i: ",".join(
                [f"{key}<{raw[key]}>" for key in raw if key in self._composite]
            )
        )

    @property
    def _id(self) -> str:
        result = next((field for field in self.fields if field.is_id), None)
        if result is None:
            raise ValueError("Id field is required.")
        return result.name

    @property
    def _composite(self) -> list[str]:
        names = [field.name for field in self.fields if field.is_composite]
        return [self._id] if len(names) == 0 else names


@dataclass(frozen=True)
class SqliteField:
    name: str
    is_id: bool
    is_composite: bool
