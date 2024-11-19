from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import IntegrityError
from typing import Any, Generic, Iterable, Iterator

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
from apexdevkit.repository import Database, DatabaseCommand, RepositoryBase
from apexdevkit.repository.interface import ItemT
from apexdevkit.repository.sql import NotNone, _SqlField


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
    fields: list[_SqlField] | None = None

    def with_name(self, value: str) -> SqliteTableBuilder[ItemT]:
        return SqliteTableBuilder[ItemT](value, self.formatter, self.fields)

    def with_formatter(
        self, value: Formatter[dict[str, Any], ItemT]
    ) -> SqliteTableBuilder[ItemT]:
        return SqliteTableBuilder[ItemT](self.table_name, value, self.fields)

    def with_fields(self, value: Iterable[_SqlField]) -> SqliteTableBuilder[ItemT]:
        key_list = list(value)
        if len([key for key in key_list if key.is_id]) != 1:
            raise ValueError("Pass only one identifier key.")
        if len([key for key in key_list if key.is_parent]) > 1:
            raise ValueError("Pass only one parent key.")
        if (
            len(
                [
                    key
                    for key in key_list
                    if not key.is_filter and isinstance(key.fixed_value, NotNone)
                ]
            )
            > 0
        ):
            raise ValueError("Only filter fields can be 'not null'.")
        return SqliteTableBuilder[ItemT](
            self.table_name,
            self.formatter,
            key_list,
        )

    def build(self) -> SqlTable[ItemT]:
        if not self.table_name or not self.formatter or not self.fields:
            raise ValueError("Parameter missing.")

        return _DefaultSqlTable(
            self.table_name,
            self.formatter,
            self.fields,
        )


@dataclass(frozen=True)
class _DefaultSqlTable(SqlTable[ItemT]):
    table_name: str
    formatter: Formatter[dict[str, Any], ItemT]
    fields: list[_SqlField]

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            SELECT count(*) as n_items
            FROM {self.table_name.upper()}
            {self._where_statement(include_id=False)};
        """).with_data(self._data_with_fixed({}))

    def insert(self, item: ItemT) -> DatabaseCommand:
        insert_columns = ", ".join(
            [field.name for field in self.fields if field.include_in_insert]
        )
        return_columns = ", ".join([field.name for field in self.fields])
        placeholders = ", ".join(
            [f":{key.name}" for key in self.fields if key.include_in_insert]
        )

        return DatabaseCommand(f"""
            INSERT INTO {self.table_name.upper()} (
                {insert_columns}
            ) VALUES (
                {placeholders}
            )
            RETURNING {return_columns};
        """).with_data(self._data_with_fixed(self.formatter.dump(item)))

    def select(self, item_id: str) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns} 
            FROM {self.table_name.upper()}
            {self._where_statement(include_id=True)};
        """).with_data(self._data_with_fixed({self._id: item_id}))

    def select_duplicate(self, item: ItemT) -> DatabaseCommand:
        raw = self.formatter.dump(item)
        columns = ", ".join([field.name for field in self.fields])

        duplicates = " AND ".join([f"{field} = :{field}" for field in self._composite])

        return DatabaseCommand(f"""
            SELECT
                {columns} 
            FROM {self.table_name.upper()}
            WHERE {duplicates};
        """).with_data({key: raw[key] for key in raw if key in self._composite})

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns}
            FROM {self.table_name.capitalize()}
            {self._where_statement(include_id=False)}
            {self._order}
        """).with_data(self._data_with_fixed({}))

    def update(self, item: ItemT) -> DatabaseCommand:
        updates = ", ".join(
            [
                f"{field.name} = :{field.name}"
                for field in self.fields
                if not field.is_id and not field.is_parent
            ]
        )

        return DatabaseCommand(f"""
            UPDATE {self.table_name.upper()}
            SET
                {updates}
            {self._where_statement(include_id=True)};
        """).with_data(self._data_with_fixed(self.formatter.dump(item)))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.upper()}
            {self._where_statement(include_id=True)};
        """).with_data(self._data_with_fixed({self._id: item_id}))

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.upper()}
            {self._where_statement(include_id=False)};
        """).with_data(self._data_with_fixed({}))

    def load(self, data: dict[str, Any]) -> ItemT:
        return self.formatter.load(data)

    def duplicate(self, item: ItemT) -> ExistsError:
        raw = self.formatter.dump(item)
        return ExistsError(item).with_duplicate(
            lambda i: ",".join(
                [f"{key}<{raw[key]}>" for key in raw if key in self._composite]
            )
        )

    def _where_statement(self, include_id: bool = False) -> str:
        statements = [
            statement
            for statement in [
                self._parent_filter(),
                self._id_filter(include_id),
                self._general_filters(),
            ]
            if statement != ""
        ]
        if len(statements) > 0:
            return "WHERE " + " AND ".join(statements)
        else:
            return ""

    def _parent_filter(self) -> str:
        result = next((key for key in self.fields if key.is_parent), None)
        if result is not None:
            if result.parent_value is None:
                return result.name + " IS NULL"
            else:
                return result.name + " = :" + result.name
        else:
            return ""

    def _id_filter(self, include_id: bool = False) -> str:
        return f"{self._id} = :{self._id}" if include_id else ""

    def _general_filters(self) -> str:
        statements: list[str] = []
        for key in self.fields:
            if key.is_filter:
                if key.filter_value is None:
                    statements.append(key.name + " IS NULL")
                elif isinstance(key.filter_value, NotNone):
                    statements.append(key.name + " IS NOT NULL")
                else:
                    statements.append(key.name + " = :" + key.name)

        return " AND ".join(statements)

    def _data_with_fixed(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in self.fields:
            if key.is_parent:
                data[key.name] = key.parent_value
            if key.is_fixed:
                data[key.name] = key.fixed_value
        return data

    @property
    def _id(self) -> str:
        result = next((key for key in self.fields if key.is_id), None)
        if result is None:
            raise ValueError("Id field is required.")
        return result.name

    @property
    def _composite(self) -> list[str]:
        names = [field.name for field in self.fields if field.is_composite]
        return [self._id] if len(names) == 0 else names

    @property
    def _order(self) -> str:
        ordering = [key.name for key in self.fields if key.is_ordered]
        if len(ordering) > 0:
            return "ORDER BY " + ", ".join(ordering)
        else:
            return ""
