from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, ContextManager, Iterable, Protocol

_RawData = dict[str, Any]


@dataclass(frozen=True)
class Database:
    connector: Connector

    def execute(self, command: DatabaseCommand) -> _CommandExecutor:
        return Database._CommandExecutor(self.connector, command)

    @dataclass(frozen=True)
    class _CommandExecutor:
        connector: Connector
        command: DatabaseCommand

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


@dataclass(frozen=True)
class DatabaseCommand:
    value: str = field(default_factory=str)
    payload: _RawData | list[_RawData] = field(default_factory=dict)

    def with_data(
        self, value: _RawData | None = None, **fields: Any
    ) -> DatabaseCommand:
        assert isinstance(self.payload, dict)

        payload = deepcopy(self.payload)
        payload.update(value or {})
        payload.update(fields)

        return DatabaseCommand(self.value, payload)

    def with_collection(self, value: list[_RawData]) -> DatabaseCommand:
        return DatabaseCommand(self.value, value)

    def __str__(self) -> str:  # pragma: no cover
        return self.value
