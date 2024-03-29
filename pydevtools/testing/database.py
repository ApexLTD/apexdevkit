from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, ContextManager, Self


@dataclass
class FakeConnector:
    commands: list[tuple[str, Any]] = field(default_factory=list)
    results: list[Any] = field(init=False, default_factory=list)

    def with_result(self, values: Any) -> Self:
        self.results = [values, *self.results]

        return self

    def execute(self, command: str, data: Any) -> None:
        self.commands.append((command, data))

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