from __future__ import annotations

import sqlite3
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import pymssql
from pymssql import Connection as _Connection
from pymssql import Cursor

from apexdevkit.repository import Connection


@dataclass(frozen=True)
class SqliteFileConnector:
    dsn: str

    def connect(self) -> AbstractContextManager[Connection]:
        connection = sqlite3.connect(self.dsn)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass(frozen=True)
class SqliteInMemoryConnector:
    dsn: str = ":memory:"

    def connect(self) -> AbstractContextManager[Connection]:
        return self._connection

    @cached_property
    def _connection(self) -> AbstractContextManager[Connection]:
        connection = sqlite3.connect(self.dsn, check_same_thread=False)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass(frozen=True)
class MsSqlConnector:
    db_host: str
    db_user: str
    db_password: str
    db_name: str
    db_tds_version = "7.0"
    db_port: str | None = None

    def connect(self) -> AbstractContextManager[Connection]:
        return ConnectionContextManager(self._connection())

    def _connection(self) -> Connection:
        connection_params = {
            "tds_version": self.db_tds_version,
            "server": self.db_host,
            "user": self.db_user,
            "password": self.db_password,
            "database": self.db_name,
            "as_dict": True,
            "autocommit": True,
        }

        if self.db_port is not None:
            connection_params["port"] = self.db_port

        return MsSqlConnectionAdapter(pymssql.connect(**connection_params))


class ConnectionContextManager(AbstractContextManager[Connection]):
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def __enter__(self) -> Connection:
        return self.connection

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.connection.cursor().close()
        self.connection.close()


@dataclass
class MsSqlConnectionAdapter:
    connection: _Connection

    def cursor(self) -> MsSqlCursorAdapter:
        return MsSqlCursorAdapter(self.connection.cursor())

    def close(self) -> None:
        self.connection.close()


@dataclass
class MsSqlCursorAdapter:
    cursor: Cursor

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        self.cursor.execute(*args, **kwargs)

    def executemany(self, *args: Any, **kwargs: Any) -> Any:
        self.cursor.executemany(*args, **kwargs)

    def fetchone(self, *_: Any, **__: Any) -> Any:
        return self.cursor.fetchone()

    def fetchall(self, *_: Any, **__: Any) -> Any:
        return self.cursor.fetchall()

    def close(self) -> None:
        self.cursor.close()  # type : ignore
