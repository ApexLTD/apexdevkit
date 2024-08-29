from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ContextManager, Iterable, Protocol, Self

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


class Connector(Protocol):  # pragma: no cover
    def connect(self) -> ContextManager[Connection]:
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
