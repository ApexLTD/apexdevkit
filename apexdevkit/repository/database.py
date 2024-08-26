from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ContextManager, Dict, Iterable, Iterator, Protocol, Self

from pymongo import MongoClient
from pymongo.collection import Collection, ReturnDocument
from pymongo.results import DeleteResult, InsertOneResult

_RawData = dict[str, Any]


@dataclass
class Database:
    connector: Connector

    command: DatabaseCommand = field(init=False)

    def execute(self, command: DatabaseCommand) -> Self:
        self.command = command

        return self

    def fetch_none(self) -> None:
        with self.connector.connect() as connection:
            cursor: Cursor = connection.cursor()
            cursor.execute(self.command.value, self.command.payload)
            cursor.close()

    def fetch_one(self) -> _RawData:
        with self.connector.connect() as connection:
            cursor: Cursor = connection.cursor()
            cursor.execute(self.command.value, self.command.payload)
            raw = cursor.fetchone()
            cursor.close()

        return dict(raw or {})

    def fetch_all(self) -> Iterable[_RawData]:
        with self.connector.connect() as connection:
            cursor: Cursor = connection.cursor()
            cursor.execute(self.command.value, self.command.payload)
            raw = cursor.fetchall()
            cursor.close()

        return [dict(raw or {}) for raw in raw]


@dataclass
class MongoDatabase:
    connector: MongoConnector
    database_name: str
    collection_name: str

    def collection(self, client: MongoClient[Any]) -> Collection[Any]:
        return client[self.database_name][self.collection_name]

    def __iter__(self) -> Iterator[Any]:
        with self.connector.connect() as client:
            for raw in self.collection(client).find():
                yield raw

    def __len__(self) -> int:
        with self.connector.connect() as client:
            return self.collection(client).count_documents({})

    def create(self, item: Dict[str, Any]) -> InsertOneResult:
        with self.connector.connect() as client:
            return self.collection(client).insert_one(item)

    def read(self, item_id: str) -> Dict[str, Any] | None:
        with self.connector.connect() as client:
            return self.collection(client).find_one({"id": item_id})

    def update(self, item_id: str, item: Dict[str, Any]) -> Any:
        with self.connector.connect() as client:
            return self.collection(client).find_one_and_update(
                {"id": item_id},
                {"$set": item},
                return_document=ReturnDocument.AFTER,
            )

    def delete(self, item_id: str) -> DeleteResult:
        with self.connector.connect() as client:
            return self.collection(client).delete_one({"id": item_id})

    def delete_all(self) -> DeleteResult:
        with self.connector.connect() as client:
            return self.collection(client).delete_many({})


class Connector(Protocol):  # pragma: no cover
    def connect(self) -> ContextManager[Connection]:
        pass


class MongoConnector(Protocol):  # pragma: no cover
    def connect(self) -> ContextManager[MongoClient[Any]]:
        pass


class Connection(Protocol):  # pragma: no cover
    def cursor(self) -> Cursor:
        pass


class Cursor(Protocol):  # pragma: no cover
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def executemany(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def fetchone(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def fetchall(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def close(self) -> None:
        pass


@dataclass
class DatabaseCommand:
    value: str
    payload: _RawData | list[_RawData] = field(init=False, default_factory=dict)

    def with_data(self, value: _RawData | None = None, **fields: Any) -> Self:
        assert isinstance(self.payload, dict)
        self.payload.update(value or {})
        self.payload.update(fields)

        return self

    def with_collection(self, value: list[_RawData]) -> Self:
        self.payload = value

        return self

    def __str__(self) -> str:  # pragma: no cover
        return self.value
