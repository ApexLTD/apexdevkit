from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, ContextManager, Self

from apexdevkit.repository import DatabaseCommand


@dataclass(frozen=True)
class FakeConnector:
    commands: list[tuple[str, Any]] = field(default_factory=list)
    results: list[Any] = field(default_factory=list)

    def with_result(self, values: Any) -> FakeConnector:
        return FakeConnector(self.commands, [values, *self.results])

    def execute(self, command: str, data: Any) -> None:
        self.commands.append((command, data))

    def executemany(self, command: str, data_list: list[Any]) -> None:
        self.commands.extend([(command, data) for data in data_list])

    def fetchone(self) -> dict[str, Any]:
        return self.results.pop()  # type: ignore

    def fetchall(self) -> list[dict[str, Any]]:
        return self.results.pop()  # type: ignore

    def connect(self) -> ContextManager[Self]:
        return nullcontext(self)

    def cursor(self) -> Self:
        return self

    def close(self) -> None:
        pass

    def assert_contains(self, command: DatabaseCommand, at_index: int = 0) -> None:
        query, data = self.commands[at_index]

        assert command == DatabaseCommand(query).with_data(data)
