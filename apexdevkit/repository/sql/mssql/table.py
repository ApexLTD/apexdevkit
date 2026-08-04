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

    def select_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def delete(self, item_id: str) -> DatabaseCommand:
        raise NotImplementedError

    def delete_all(self) -> DatabaseCommand:
        raise NotImplementedError

    def update(self, item: T) -> DatabaseCommand:
        raise NotImplementedError

    def load(self, data: Mapping[str, Any]) -> T:
        raise NotImplementedError

    def exists(self, duplicate: T) -> ExistsError:
        raise NotImplementedError


@dataclass
class SqlTableDecorator[T]:
    table: DefaultSqlTable[T]

    def count_all(self) -> DatabaseCommand:
        return self.table.count_all()

    def insert(self, item: T) -> DatabaseCommand:
        return self.table.insert(item)

    def select(self, item_id: str) -> DatabaseCommand:
        return self.table.select(item_id)

    def select_all(self) -> DatabaseCommand:
        return self.table.select_all()

    def delete(self, item_id: str) -> DatabaseCommand:
        return self.table.delete(item_id)

    def delete_all(self) -> DatabaseCommand:
        return self.table.delete_all()

    def update(self, item: T) -> DatabaseCommand:
        return self.table.update(item)

    def load(self, data: dict[str, Any]) -> T:
        return self.table.load(data)

    def exists(self, duplicate: T) -> ExistsError:
        return self.table.exists(duplicate)


@dataclass(frozen=True)
class MsSqlTableBuilder[T]:
    username: str | None = None
    schema: str | None = None
    table: str | None = None
    formatter: Formatter[Mapping[str, Any], T] | None = None
    fields: list[_SqlField] | None = None
    custom_filters: list[str] | None = None

    def with_username(self, value: str) -> MsSqlTableBuilder[T]:
        return MsSqlTableBuilder[T](
            value,
            self.schema,
            self.table,
            self.formatter,
            self.fields,
            self.custom_filters,
        )

    def with_schema(self, value: str) -> MsSqlTableBuilder[T]:
        return MsSqlTableBuilder[T](
            self.username,
            value,
            self.table,
            self.formatter,
            self.fields,
            self.custom_filters,
        )

    def with_table(self, value: str) -> MsSqlTableBuilder[T]:
        return MsSqlTableBuilder[T](
            self.username,
            self.schema,
            value,
            self.formatter,
            self.fields,
            self.custom_filters,
        )

    def with_formatter(
        self, value: Formatter[Mapping[str, Any], T]
    ) -> MsSqlTableBuilder[T]:
        return MsSqlTableBuilder[T](
            self.username,
            self.schema,
            self.table,
            value,
            self.fields,
            self.custom_filters,
        )

    def with_fields(self, value: Iterable[_SqlField]) -> MsSqlTableBuilder[T]:
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
        return MsSqlTableBuilder[T](
            self.username,
            self.schema,
            self.table,
            self.formatter,
            key_list,
            self.custom_filters,
        )

    def with_custom_filters(self, filters: Iterable[str]) -> MsSqlTableBuilder[T]:
        return MsSqlTableBuilder[T](
            self.username,
            self.schema,
            self.table,
            self.formatter,
            self.fields,
            list(filters),
        )

    def build(self) -> SqlTable[T]:
        if not self.schema or not self.table or not self.formatter or not self.fields:
            raise ValueError("Cannot build sql table.")

        field_manager = SqlFieldManager.Builder().with_fields(self.fields)
        if self.custom_filters and len(self.custom_filters) > 0:
            field_manager = field_manager.with_custom_filters(self.custom_filters)

        return DefaultSqlTable(
            self.schema,
            self.table,
            self.formatter,
            field_manager.for_mssql().build(),
            self.username,
        )


@dataclass(frozen=True)
class DefaultSqlTable[T](SqlTable[T]):
    schema: str
    table: str
    formatter: Formatter[Mapping[str, Any], T]
    fields: SqlFieldManager
    username: str | None = None

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            SELECT count(*) AS n_items
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def insert(self, item: T) -> DatabaseCommand:
        columns = ", ".join(
            ["[" + field.name + "]" for field in self.fields if field.include_in_insert]
        )
        placeholders = ", ".join(
            [f"%({key.name})s" for key in self.fields if key.include_in_insert]
        )
        try:
            _ = self.fields.id
            output = ", ".join(
                ["[" + field.name + "] AS " + field.name for field in self.fields]
            )
            where_statement = f"""
                FROM [{self.schema}].[{self.table}]
                {self.fields.where_statement(include_id=True, read_id=True)}
            """
        except ValueError:
            output = ", ".join(
                ["%(" + field.name + ")s AS " + field.name for field in self.fields]
            )
            where_statement = ""

        return DatabaseCommand(f"""
            {self._user_check}
            INSERT INTO [{self.schema}].[{self.table}] (
                {columns}
            )
            VALUES (
                {placeholders}
            );
            SELECT
                {output}
            {where_statement}
            REVERT
        """).with_data(self.fields.with_fixed(self.formatter.dump(item)))

    def select(self, item_id: str) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
                {columns}
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed({self.fields.id: item_id}))

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
                {columns}
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            {self.fields.order}
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def update(self, item: T) -> DatabaseCommand:
        updates = ", ".join(
            [
                f"{field.name} = %({field.name})s"
                for field in self.fields
                if not field.is_id and not field.is_parent and field.include_in_update
            ]
        )

        return DatabaseCommand(f"""
            {self._user_check}
            UPDATE [{self.schema}].[{self.table}]
            SET
                {updates}
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed(self.formatter.dump(item)))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed({self.fields.id: item_id}))

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def load(self, data: Mapping[str, Any]) -> T:
        return self.formatter.load(data)

    def exists(self, duplicate: T) -> ExistsError:
        raw = self.formatter.dump(duplicate)
        return ExistsError(duplicate).with_duplicate(
            lambda _: f"{self.fields.id}<{raw[self.fields.id]}>"
        )

    @property
    def _user_check(self) -> str:
        if self.username is not None:
            return f"EXECUTE AS USER = '{self.username}'"
        return ""
