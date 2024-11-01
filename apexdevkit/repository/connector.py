from __future__ import annotations

import sqlite3
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import cached_property
from typing import Any, ContextManager

import pymssql
from pymongo import MongoClient
from pymssql import Connection as _Connection
from pymssql import Cursor

from apexdevkit.repository import Connection


@dataclass(frozen=True)
class SqliteFileConnector:
    dsn: str

    def connect(self) -> ContextManager[Connection]:
        connection = sqlite3.connect(self.dsn)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass(frozen=True)
class SqliteInMemoryConnector:
    dsn: str = ":memory:"

    def connect(self) -> ContextManager[Connection]:
        return self._connection

    @cached_property
    def _connection(self) -> ContextManager[Connection]:
        connection = sqlite3.connect(self.dsn, check_same_thread=False)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass(frozen=True)
class PyMongoConnector:
    dsn: str

    def connect(self) -> ContextManager[MongoClient[Any]]:
        return MongoClient(self.dsn)


@dataclass(frozen=True)
class MsSqlConnector:
    db_host: str
    db_user: str
    db_password: str
    db_name: str
    db_tds_version = "7.0"

    def connect(self) -> ContextManager[Connection]:
        return ConnectionContextManager(self._connection())

    def _connection(self) -> Connection:
        return MsSqlConnectionAdapter(
            pymssql.connect(
                tds_version=self.db_tds_version,
                server=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                as_dict=True,
                autocommit=True,
            )
        )


class ConnectionContextManager(AbstractContextManager[Connection]):
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def __enter__(self) -> Connection:
        return self.connection

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.connection.cursor().close()


@dataclass
class MsSqlConnectionAdapter:
    connection: _Connection

    def cursor(self) -> MsSqlCursorAdapter:
        return MsSqlCursorAdapter(self.connection.cursor())


@dataclass
class MsSqlCursorAdapter:
    cursor: Cursor

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        self.cursor.execute(*args, **kwargs)  # type : ignore

    def executemany(self, *args: Any, **kwargs: Any) -> Any:
        self.cursor.executemany(*args, **kwargs)  # type : ignore

    def fetchone(self, *args: Any, **kwargs: Any) -> Any:
        return self.cursor.fetchone()  # type : ignore

    def fetchall(self, *args: Any, **kwargs: Any) -> Any:
        return self.cursor.fetchall()  # type : ignore

    def close(self) -> None:
        self.cursor.close()  # type : ignore
