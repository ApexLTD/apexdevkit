from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Self

from apexdevkit.annotation import deprecated
from apexdevkit.error import ExistsError
from apexdevkit.formatter import NoFormatter
from apexdevkit.repository.core import DatabaseCommand
from apexdevkit.repository.sql.field import NotNone, SqlFieldManager, _SqlField

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from apexdevkit.formatter import Formatter


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

    def exists(self, duplicate: T) -> ExistsError:
        return ExistsError(duplicate).with_duplicate(lambda _: "Unknown")


@dataclass(frozen=True)
class SqlFieldSet:
    items: list[_SqlField] = field(init=False, default_factory=list)

    def __iter__(self) -> Iterator[_SqlField]:
        return iter(self.items)

    def contains_id(self) -> bool:
        return any(i.is_id for i in self.items)

    def add(self, item: _SqlField) -> Self:
        self.items.append(self.validate(item))

        return self

    def validate(self, item: _SqlField) -> _SqlField:
        if item.is_id and self.contains_id():
            raise ValueError("Pass only one identifier key.")

        if item.is_parent and any(i.is_parent for i in self.items):
            raise ValueError("Pass only one parent key.")

        if not item.is_filter and isinstance(item.fixed_value, NotNone):
            raise ValueError("Only filter fields can be 'not null'.")

        return item


@dataclass(frozen=True)
class MsSqlTableBuilder[T]:
    username: str | None = None
    schema: str | None = None
    table: str | None = None

    fields: SqlFieldSet = field(default_factory=SqlFieldSet)
    custom_filters: list[str] = field(default_factory=list)

    formatter: Formatter[Mapping[str, Any], T] = field(default_factory=NoFormatter)

    def with_username(self, value: str) -> Self:
        return replace(self, username=value)

    def with_schema(self, value: str) -> Self:
        return replace(self, schema=value)

    def with_table(self, value: str) -> Self:
        return replace(self, table=value)

    @deprecated("Use .build().with_a(formatter) instead")
    def with_formatter(self, value: Formatter[Mapping[str, Any], T]) -> Self:
        return replace(self, formatter=value)

    @deprecated("Use .with_a/and_a method(s) instead")
    def with_fields(self, value: Iterable[_SqlField]) -> Self:
        for sql_field in value:
            self.with_a(sql_field=sql_field)

        return self

    def and_a(self, sql_field: _SqlField) -> Self:
        return self.with_a(sql_field=sql_field)

    def with_a(self, sql_field: _SqlField) -> Self:
        self.fields.add(sql_field)

        return self

    def with_custom_filters(self, filters: Iterable[str]) -> Self:
        return replace(self, custom_filters=list(filters))

    def build(self) -> AutoMsSqlTable[T]:
        if not self.fields.contains_id():
            raise ValueError("Id field is not provided!")

        if not self.schema or not self.table:
            raise ValueError("Cannot build sql table.")

        return AutoMsSqlTable(
            username=self.username,
            schema=self.schema,
            table=self.table,
            fields=(
                SqlFieldManager.Builder()
                .with_fields(list(self.fields))
                .with_custom_filters(list(self.custom_filters))
                .for_mssql()
                .build()
            ),
        ).with_a(formatter=self.formatter)


@dataclass(frozen=True, kw_only=True)
class AutoMsSqlTable[T](SqlTable[T]):
    schema: str
    table: str
    fields: SqlFieldManager

    username: str | None = None

    formatter: Formatter[Mapping[str, Any], T] = field(default_factory=NoFormatter)

    def with_a(self, formatter: Formatter[Mapping[str, Any], T]) -> AutoMsSqlTable[T]:
        return replace(self, formatter=formatter)

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
        if not self.username:
            return ""

        return f"EXECUTE AS USER = '{self.username}'"
