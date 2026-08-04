from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from apexdevkit.error import ExistsError
from apexdevkit.formatter import Formatter
from apexdevkit.repository.core import DatabaseCommand
from apexdevkit.repository.sql.field import NotNone, SqlFieldManager, _SqlField


class SqlTable[T]:  # pragma: no cover
    def count_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def insert(self, item: T) -> DatabaseCommand:
        raise NotImplementedError

    def select(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def select_duplicate(self, item: T) -> DatabaseCommand:
        raise NotImplementedError

    def select_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def update(self, item: T) -> DatabaseCommand:
        raise NotImplementedError

    def delete(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def delete_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def load(self, data: Mapping[str, Any]) -> T:
        raise NotImplementedError

    def duplicate(self, item: T) -> ExistsError:
        return ExistsError(item).with_duplicate(lambda _: "Unknown")


@dataclass(frozen=True)
class SqliteTableBuilder[T]:
    table_name: str | None = None
    formatter: Formatter[Mapping[str, Any], T] | None = None
    fields: list[_SqlField] | None = None
    custom_filters: list[str] | None = None

    def with_name(self, value: str) -> SqliteTableBuilder[T]:
        return SqliteTableBuilder[T](
            value,
            self.formatter,
            self.fields,
            self.custom_filters,
        )

    def with_formatter(
        self, value: Formatter[Mapping[str, Any], T]
    ) -> SqliteTableBuilder[T]:
        return SqliteTableBuilder[T](
            self.table_name,
            value,
            self.fields,
            self.custom_filters,
        )

    def with_fields(self, value: Iterable[_SqlField]) -> SqliteTableBuilder[T]:
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
        return SqliteTableBuilder[T](
            self.table_name,
            self.formatter,
            key_list,
            self.custom_filters,
        )

    def with_custom_filters(self, filters: Iterable[str]) -> SqliteTableBuilder[T]:
        return SqliteTableBuilder[T](
            self.table_name,
            self.formatter,
            self.fields,
            list(filters),
        )

    def build(self) -> SqlTable[T]:
        if not self.table_name or not self.formatter or not self.fields:
            raise ValueError("Parameter missing.")

        field_manager = SqlFieldManager.Builder().with_fields(self.fields)
        if self.custom_filters and len(self.custom_filters) > 0:
            field_manager = field_manager.with_custom_filters(self.custom_filters)

        return _DefaultSqlTable(
            self.table_name,
            self.formatter,
            field_manager.for_sqlite().build(),
        )


@dataclass(frozen=True)
class _DefaultSqlTable[T](SqlTable[T]):
    table_name: str
    formatter: Formatter[Mapping[str, Any], T]
    fields: SqlFieldManager

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            SELECT count(*) as n_items
            FROM {self.table_name.upper()}
            {self.fields.where_statement(include_id=False)};
        """).with_data(self.fields.with_fixed({}))

    def insert(self, item: T) -> DatabaseCommand:
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
        """).with_data(self.fields.with_fixed(self.formatter.dump(item)))

    def select(self, item_id: str) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns}
            FROM {self.table_name.upper()}
            {self.fields.where_statement(include_id=True)};
        """).with_data(self.fields.with_fixed({self.fields.id: item_id}))

    def select_duplicate(self, item: T) -> DatabaseCommand:
        raw = self.formatter.dump(item)
        columns = ", ".join([field.name for field in self.fields])

        duplicates = " AND ".join(
            [f"{field} = :{field}" for field in self.fields.composite]
        )

        return DatabaseCommand(f"""
            SELECT
                {columns}
            FROM {self.table_name.upper()}
            WHERE {duplicates};
        """).with_data({key: raw[key] for key in raw if key in self.fields.composite})

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join([field.name for field in self.fields])

        return DatabaseCommand(f"""
            SELECT
                {columns}
            FROM {self.table_name.capitalize()}
            {self.fields.where_statement(include_id=False)}
            {self.fields.order}
        """).with_data(self.fields.with_fixed({}))

    def update(self, item: T) -> DatabaseCommand:
        updates = ", ".join(
            [
                f"{field.name} = :{field.name}"
                for field in self.fields
                if not field.is_id and not field.is_parent and field.include_in_update
            ]
        )

        return DatabaseCommand(f"""
            UPDATE {self.table_name.upper()}
            SET
                {updates}
            {self.fields.where_statement(include_id=True)};
        """).with_data(self.fields.with_fixed(self.formatter.dump(item)))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.upper()}
            {self.fields.where_statement(include_id=True)};
        """).with_data(self.fields.with_fixed({self.fields.id: item_id}))

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            DELETE
            FROM {self.table_name.upper()}
            {self.fields.where_statement(include_id=False)};
        """).with_data(self.fields.with_fixed({}))

    def load(self, data: Mapping[str, Any]) -> T:
        return self.formatter.load(data)

    def duplicate(self, item: T) -> ExistsError:
        raw = self.formatter.dump(item)
        return ExistsError(item).with_duplicate(
            lambda _: ",".join(
                [f"{key}<{raw[key]}>" for key in raw if key in self.fields.composite]
            )
        )
