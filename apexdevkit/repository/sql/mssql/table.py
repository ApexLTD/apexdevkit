from __future__ import annotations

from dataclasses import dataclass, field, replace
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self

from apexdevkit.error import ExistsError
from apexdevkit.formatter import NoFormatter
from apexdevkit.repository.core import DatabaseCommand
from apexdevkit.repository.sql.field import SqlField, SqlFieldManager, SqlFieldSet

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
class MsSqlTableBuilder[T]:
    schema: str = ""
    table: str = ""

    fields: SqlFieldSet = field(default_factory=SqlFieldSet)
    custom_filters: list[str] = field(default_factory=list)

    def with_schema(self, value: str) -> Self:
        return replace(self, schema=value)

    def with_table(self, value: str) -> Self:
        return replace(self, table=value)

    def and_a(self, sql_field: SqlField) -> Self:
        return self.with_a(sql_field=sql_field)

    def with_a(self, sql_field: SqlField) -> Self:
        self.fields.add(sql_field)

        return self

    def with_custom_filters(self, filters: Iterable[str]) -> Self:
        return replace(self, custom_filters=list(filters))

    def build(self) -> AutoMsSqlTable[T]:
        if not self.fields.contains_id():
            raise ValueError("Id field is not provided!")

        if not self.schema or not self.table:
            raise ValueError("Cannot build sql table.")

        fields = (
            SqlFieldManager.Builder.for_mssql()
            .with_fields(self.fields)
            .with_custom_filters(list(self.custom_filters))
            .build()
        )

        return AutoMsSqlTable[T](
            fields=fields,
            templates=SqlTemplates(
                schema=self.schema,
                table=self.table,
                fields=fields,
            ),
        )


@dataclass(frozen=True, kw_only=True)
class AutoMsSqlTable[T](SqlTable[T]):
    fields: SqlFieldManager
    templates: SqlTemplates

    formatter: Formatter[Mapping[str, Any], T] = field(default_factory=NoFormatter)

    def with_a(self, formatter: Formatter[Mapping[str, Any], T]) -> AutoMsSqlTable[T]:
        return replace(self, formatter=formatter)

    def for_a(self, username: str) -> AutoMsSqlTable[T] | AsUser[T]:
        if not username:
            return self

        return AsUser(user=username, inner=self)

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.count_all(),
            payload=self.fields.with_fixed({}),
        )

    def insert(self, item: T) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.insert(),
            payload=self.fields.with_fixed(self.formatter.dump(item)),
        )

    def select(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.select(),
            payload=self.fields.with_fixed({self.fields.id: item_id}),
        )

    def select_all(self) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.select_all(),
            payload=self.fields.with_fixed({}),
        )

    def update(self, item: T) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.update(),
            payload=self.fields.with_fixed(self.formatter.dump(item)),
        )

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.delete(),
            payload=self.fields.with_fixed({self.fields.id: item_id}),
        )

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(
            value=self.templates.delete_all(),
            payload=self.fields.with_fixed({}),
        )

    def load(self, data: Mapping[str, Any]) -> T:
        return self.formatter.load(data)

    def exists(self, duplicate: T) -> ExistsError:
        raw = self.formatter.dump(duplicate)
        return ExistsError(duplicate).with_duplicate(
            lambda _: f"{self.fields.id}<{raw[self.fields.id]}>"
        )


@dataclass(frozen=True, kw_only=True)
class SqlTemplates:
    schema: str
    table: str
    fields: SqlFieldManager

    def count_all(self) -> str:
        return f"""
            SELECT count(*) AS n_items
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            REVERT
        """

    def insert(self) -> str:
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

        return f"""
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
        """

    def select(self) -> str:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return f"""
            SELECT
                {columns}
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """

    def select_all(self) -> str:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return f"""
            SELECT
                {columns}
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            {self.fields.order}
            REVERT
        """

    def update(self) -> str:
        updates = ", ".join(
            [
                f"{field.name} = %({field.name})s"
                for field in self.fields
                if not field.is_id and not field.is_parent and field.include_in_update
            ]
        )

        return f"""
            UPDATE [{self.schema}].[{self.table}]
            SET
                {updates}
            {self.fields.where_statement(include_id=True)}
            REVERT
        """

    def delete(self) -> str:
        return f"""
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """

    def delete_all(self) -> str:
        return f"""
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self.fields.where_statement(include_id=False)}
            REVERT
        """


@dataclass(frozen=True, kw_only=True)
class AsUser[T](SqlTable[T]):
    user: str

    inner: AutoMsSqlTable[T]

    def __post_init__(self) -> None:
        if not self.user:
            raise ValueError("username must be provided")

    def _wrap(self, command: DatabaseCommand) -> DatabaseCommand:
        return DatabaseCommand(
            "\n".join(
                [
                    f"EXECUTE AS USER = '{self.user}'",
                    dedent(command.value),
                ]
            ),
            payload=command.payload,
        )

    def count_all(self) -> DatabaseCommand:
        return self._wrap(self.inner.count_all())

    def insert(self, item: T) -> DatabaseCommand:
        return self._wrap(self.inner.insert(item))

    def select(self, item_id: str) -> DatabaseCommand:
        return self._wrap(self.inner.select(item_id))

    def select_all(self) -> DatabaseCommand:
        return self._wrap(self.inner.select_all())

    def update(self, item: T) -> DatabaseCommand:
        return self._wrap(self.inner.update(item))

    def delete(self, item_id: str) -> DatabaseCommand:
        return self._wrap(self.inner.delete(item_id))

    def delete_all(self) -> DatabaseCommand:
        return self._wrap(self.inner.delete_all())

    def load(self, data: Mapping[str, Any]) -> T:
        return self.inner.load(data)

    def exists(self, duplicate: T) -> ExistsError:
        return self.inner.exists(duplicate)
