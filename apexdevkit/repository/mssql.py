from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Iterator, Mapping, TypeVar

from pymssql.exceptions import DatabaseError

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
from apexdevkit.repository import Database, DatabaseCommand, RepositoryBase
from apexdevkit.repository.sql import NotNone, SqlFieldManager, _SqlField

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

    def load(self, data: Mapping[str, Any]) -> ItemT:
        raise NotImplementedError

    def exists(self, duplicate: ItemT) -> ExistsError:
        raise NotImplementedError


@dataclass
class SqlTableDecorator(Generic[ItemT]):
    table: DefaultSqlTable[ItemT]

    def count_all(self) -> DatabaseCommand:
        return self.table.count_all()

    def insert(self, item: ItemT) -> DatabaseCommand:
        return self.table.insert(item)

    def select(self, item_id: str) -> DatabaseCommand:
        return self.table.select(item_id)

    def select_all(self) -> DatabaseCommand:
        return self.table.select_all()

    def delete(self, item_id: str) -> DatabaseCommand:
        return self.table.delete(item_id)

    def delete_all(self) -> DatabaseCommand:
        return self.table.delete_all()

    def update(self, item: ItemT) -> DatabaseCommand:
        return self.table.update(item)

    def load(self, data: dict[str, Any]) -> ItemT:
        return self.table.load(data)

    def exists(self, duplicate: ItemT) -> ExistsError:
        return self.table.exists(duplicate)


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


@dataclass(frozen=True)
class MsSqlTableBuilder(Generic[ItemT]):
    username: str | None = None
    schema: str | None = None
    tables: list[str] = field(default_factory=list)
    formatter: Formatter[Mapping[str, Any], ItemT] | None = None
    fields: list[_SqlField] | None = None
    table_mapper: Callable[[ItemT], str] | None = None
    table_id_mapper: Callable[[str], str] | None = None
    id_transformer: Callable[[str], str] = lambda identifier: identifier

    def with_username(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            value,
            self.schema,
            self.tables,
            self.formatter,
            self.fields,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )

    def with_schema(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            value,
            self.tables,
            self.formatter,
            self.fields,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )

    def with_table(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables + [value],
            self.formatter,
            self.fields,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )

    def and_table(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return self.with_table(value)

    def with_table_mapper(
        self, value: Callable[[ItemT], str]
    ) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables,
            self.formatter,
            self.fields,
            value,
            self.table_id_mapper,
            self.id_transformer,
        )

    def with_table_id_mapper(
        self, value: Callable[[str], str]
    ) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables,
            self.formatter,
            self.fields,
            self.table_mapper,
            value,
            self.id_transformer,
        )

    def with_id_transformer(
        self, value: Callable[[str], str]
    ) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables,
            self.formatter,
            self.fields,
            self.table_mapper,
            self.table_id_mapper,
            value,
        )

    def with_formatter(
        self, value: Formatter[Mapping[str, Any], ItemT]
    ) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables,
            value,
            self.fields,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )

    def with_fields(self, value: Iterable[_SqlField]) -> MsSqlTableBuilder[ItemT]:
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
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.tables,
            self.formatter,
            key_list,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )

    def build(self) -> SqlTable[ItemT]:
        if (
            not self.schema
            or len(self.tables) < 1
            or not self.formatter
            or not self.fields
        ):
            raise ValueError("Cannot build sql table.")

        return DefaultSqlTable(
            self.schema,
            self.tables,
            self.formatter,
            SqlFieldManager.Builder().with_fields(self.fields).for_mssql().build(),
            self.username,
            self.table_mapper,
            self.table_id_mapper,
            self.id_transformer,
        )


@dataclass(frozen=True)
class DefaultSqlTable(SqlTable[ItemT]):
    schema: str
    tables: list[str]
    formatter: Formatter[Mapping[str, Any], ItemT]
    fields: SqlFieldManager
    username: str | None = None
    table_mapper: Callable[[ItemT], str] | None = None
    table_id_mapper: Callable[[str], str] | None = None
    id_transformer: Callable[[str], str] = lambda identifier: identifier

    def count_all(self) -> DatabaseCommand:
        selections = " + ".join(
            [
                f"""(
                SELECT COUNT(*)
                FROM [{self.schema}].[{table}]
                {self.fields.where_statement(include_id=False)}
            )"""
                for table in self.tables
            ]
        )
        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
            {selections} AS n_items
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def insert(self, item: ItemT) -> DatabaseCommand:
        self._require_mapper_if_necessary()

        columns = ", ".join(
            ["[" + field.name + "]" for field in self.fields if field.include_in_insert]
        )
        placeholders = ", ".join(
            [f"%({key.name})s" for key in self.fields if key.include_in_insert]
        )
        try:
            self.fields.id
            output = ", ".join(
                ["[" + field.name + "] AS " + field.name for field in self.fields]
            )
            where_statement = f"""
                FROM [{self.schema}].[{self._determine_table_by_item(item)}]
                {self.fields.where_statement(include_id=True, read_id=True)}
            """
        except ValueError:
            output = ", ".join(
                ["%(" + field.name + ")s AS " + field.name for field in self.fields]
            )
            where_statement = ""

        return DatabaseCommand(f"""
            {self._user_check}
            INSERT INTO [{self.schema}].[{self._determine_table_by_item(item)}] (
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
        self._require_id_mapper_if_necessary()

        columns = ", ".join(["[" + field.name + "]" for field in self.fields])
        table_identifier = self.id_transformer(item_id)

        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
                {columns} 
            FROM [{self.schema}].[{self._determine_table_by_id(item_id)}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed({self.fields.id: table_identifier}))

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        selections = """
            UNION ALL
            """.join(
            [
                f"""SELECT
                {columns}
            FROM [{self.schema}].[{table}]
            {self.fields.where_statement(include_id=False)}"""
                for table in self.tables
            ]
        )

        return DatabaseCommand(f"""
            {self._user_check}
            {selections}
            {self.fields.order}
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def update(self, item: ItemT) -> DatabaseCommand:
        self._require_mapper_if_necessary()

        updates = ", ".join(
            [
                f"{field.name} = %({field.name})s"
                for field in self.fields
                if not field.is_id and not field.is_parent and field.include_in_update
            ]
        )

        return DatabaseCommand(f"""
            {self._user_check}
            UPDATE [{self.schema}].[{self._determine_table_by_item(item)}]
            SET
                {updates}
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed(self.formatter.dump(item)))

    def delete(self, item_id: str) -> DatabaseCommand:
        self._require_mapper_if_necessary()

        table_identifier = self.id_transformer(item_id)

        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self._determine_table_by_id(item_id)}]
            {self.fields.where_statement(include_id=True)}
            REVERT
        """).with_data(self.fields.with_fixed({self.fields.id: table_identifier}))

    def delete_all(self) -> DatabaseCommand:
        if len(self.tables) > 1:
            raise RuntimeError(
                f"Deletion of multiple tables {self.tables} not supported"
            )

        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self.tables[0]}]
            {self.fields.where_statement(include_id=False)}
            REVERT
        """).with_data(self.fields.with_fixed({}))

    def load(self, data: Mapping[str, Any]) -> ItemT:
        return self.formatter.load(data)

    def exists(self, duplicate: ItemT) -> ExistsError:
        raw = self.formatter.dump(duplicate)
        return ExistsError(duplicate).with_duplicate(
            lambda i: f"{self.fields.id}<{raw[self.fields.id]}>"
        )

    def _require_mapper_if_necessary(self) -> None:
        if len(self.tables) > 1 and self.table_mapper is None:
            raise RuntimeError(
                f"Attempt to use multiple tables {self.tables} "
                f"on insert or update when mapping not provided"
            )

    def _require_id_mapper_if_necessary(self) -> None:
        if len(self.tables) > 1 and self.table_id_mapper is None:
            raise RuntimeError(
                f"Attempt to use multiple tables {self.tables} "
                f"on read or delete when id mapping not provided"
            )

    def _determine_table_by_item(self, item: ItemT) -> str:
        if len(self.tables) == 1 or self.table_mapper is None:
            return self.tables[0]
        else:
            table = self.table_mapper(item)
            if table not in self.tables:
                raise RuntimeError(f"Illegal table {table} provided")
            return table

    def _determine_table_by_id(self, identifier: str) -> str:
        if len(self.tables) == 1 or self.table_id_mapper is None:
            return self.tables[0]
        else:
            table = self.table_id_mapper(identifier)
            if table not in self.tables:
                raise RuntimeError(f"Illegal table {table} provided")
            return table

    @property
    def _user_check(self) -> str:
        if self.username is not None:
            return f"EXECUTE AS USER = '{self.username}'"
        else:
            return ""
