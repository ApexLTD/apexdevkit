from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Iterable, Iterator, TypeVar

from pymssql.exceptions import DatabaseError

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
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
    table: str | None = None
    formatter: Formatter[dict[str, Any], ItemT] | None = None
    fields: list[MsSqlField] | None = None

    def with_username(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            value,
            self.schema,
            self.table,
            self.formatter,
            self.fields,
        )

    def with_schema(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            value,
            self.table,
            self.formatter,
            self.fields,
        )

    def with_table(self, value: str) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            value,
            self.formatter,
            self.fields,
        )

    def with_formatter(
        self, value: Formatter[dict[str, Any], ItemT]
    ) -> MsSqlTableBuilder[ItemT]:
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.table,
            value,
            self.fields,
        )

    def with_fields(self, value: Iterable[MsSqlField]) -> MsSqlTableBuilder[ItemT]:
        field_list = list(value)
        if len([field for field in field_list if field.is_id]) != 1:
            raise ValueError("Pass only one identifier field.")
        if len([field for field in field_list if field.is_parent]) > 1:
            raise ValueError("Pass only one parent field.")
        return MsSqlTableBuilder[ItemT](
            self.username,
            self.schema,
            self.table,
            self.formatter,
            field_list,
        )

    def build(self) -> SqlTable[ItemT]:
        if not self.schema or not self.table or not self.formatter or not self.fields:
            raise ValueError("Cannot build sql table.")

        return DefaultSqlTable(
            self.schema,
            self.table,
            self.formatter,
            self.fields,
            self.username,
        )


@dataclass(frozen=True)
class DefaultSqlTable(SqlTable[ItemT]):
    schema: str
    table: str
    formatter: Formatter[dict[str, Any], ItemT]
    fields: list[MsSqlField]
    username: str | None = None

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            SELECT count(*) AS n_items
            FROM [{self.schema}].[{self.table}]
            {self._where_statement(include_id=False)}
            REVERT
        """).with_data(self._data_with_replaced_parent({}))

    def insert(self, item: ItemT) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])
        placeholders = ", ".join([f"%({key.name})s" for key in self.fields])
        output = ", ".join(["INSERTED." + field.name for field in self.fields])

        return DatabaseCommand(f"""
            {self._user_check}
            INSERT INTO [{self.schema}].[{self.table}] (
                {columns}
            ) OUTPUT
                {output}
            VALUES (
                {placeholders}
            )
            REVERT
        """).with_data(self._data_with_replaced_parent(self.formatter.dump(item)))

    def select(self, item_id: str) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
                {columns} 
            FROM [{self.schema}].[{self.table}]
            {self._where_statement(include_id=True)}
            REVERT
        """).with_data(self._data_with_replaced_parent({self._id: item_id}))

    def select_all(self) -> DatabaseCommand:
        columns = ", ".join(["[" + field.name + "]" for field in self.fields])

        return DatabaseCommand(f"""
            {self._user_check}
            SELECT
                {columns}
            FROM [{self.schema}].[{self.table}]
            {self._where_statement(include_id=False)}
            {self._order}
            REVERT
        """).with_data(self._data_with_replaced_parent({}))

    def update(self, item: ItemT) -> DatabaseCommand:
        updates = ", ".join(
            [
                f"{field.name} = %({field.name})s"
                for field in self.fields
                if not field.is_id and not field.is_parent
            ]
        )

        return DatabaseCommand(f"""
            {self._user_check}
            UPDATE [{self.schema}].[{self.table}]
            SET
                {updates}
            {self._where_statement(include_id=True)}
            REVERT
        """).with_data(self._data_with_replaced_parent(self.formatter.dump(item)))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self._where_statement(include_id=True)}
            REVERT
        """).with_data(self._data_with_replaced_parent({self._id: item_id}))

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self._user_check}
            DELETE
            FROM [{self.schema}].[{self.table}]
            {self._where_statement(include_id=False)}
            REVERT
        """).with_data(self._data_with_replaced_parent({}))

    def load(self, data: dict[str, Any]) -> ItemT:
        return self.formatter.load(data)

    def exists(self, duplicate: ItemT) -> ExistsError:
        raw = self.formatter.dump(duplicate)
        return ExistsError(duplicate).with_duplicate(
            lambda i: f"{self._id}<{raw[self._id]}>"
        )

    def _where_statement(self, include_id: bool = False) -> str:
        result = next((field for field in self.fields if field.is_parent), None)
        if result is None:
            return f"WHERE [{self._id}] = %({self._id})s" if include_id else ""
        else:
            statement = "WHERE [" + result.name + "] = %(" + result.name + ")s"
            if include_id:
                statement += f" AND [{self._id}] = %({self._id})s"
            return statement

    def _data_with_replaced_parent(self, data: dict[str, Any]) -> dict[str, Any]:
        result = next((field for field in self.fields if field.is_parent), None)
        if result is not None:
            data[result.name] = result.fixed_value
        return data

    @property
    def _id(self) -> str:
        result = next((field for field in self.fields if field.is_id), None)
        if result is None:
            raise ValueError("Id field is required.")
        return result.name

    @property
    def _user_check(self) -> str:
        if self.username is not None:
            return f"EXECUTE AS USER = '{self.username}'"
        else:
            return ""

    @property
    def _order(self) -> str:
        ordering = [field.name for field in self.fields if field.is_ordered]
        if len(ordering) > 0:
            return "ORDER BY " + ", ".join(ordering)
        else:
            return ""


@dataclass(frozen=True)
class MsSqlField:
    name: str
    is_id: bool = False
    is_ordered: bool = False

    is_parent: bool = False
    fixed_value: Any | None = None
