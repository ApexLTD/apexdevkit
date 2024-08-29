import sqlite3
from dataclasses import dataclass
from functools import cached_property
from typing import Any, ContextManager

from pymongo import MongoClient

from apexdevkit.repository import Connection


@dataclass
class SqliteFileConnector:
    dsn: str

    def connect(self) -> ContextManager[Connection]:
        connection = sqlite3.connect(self.dsn)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass
class SqliteInMemoryConnector:
    dsn: str = ":memory:"

    def connect(self) -> ContextManager[Connection]:
        return self._connection

    @cached_property
    def _connection(self) -> ContextManager[Connection]:
        connection = sqlite3.connect(self.dsn, check_same_thread=False)
        connection.row_factory = sqlite3.Row

        return connection


@dataclass
class PyMongoConnector:
    dsn: str

    def connect(self) -> ContextManager[MongoClient[Any]]:
        return MongoClient(self.dsn)
