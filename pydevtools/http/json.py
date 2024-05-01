from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar


class JsonDict(dict[str, Any]):
    def value_of(self, key: str) -> FluentElement:
        return FluentElement(self[key])

    def and_a(self, **fields: Any) -> JsonDict:
        return self.with_a(**fields)

    def with_a(self, **fields: Any) -> JsonDict:
        return self.merge(JsonDict(fields))

    def merge(self, other: JsonDict) -> JsonDict:
        return JsonDict({**self, **other})

    def drop(self, *keys: str) -> JsonDict:
        return self.select(*set(self.keys()).difference(keys))

    def select(self, *keys: str) -> JsonDict:
        return JsonDict({k: v for k, v in self.items() if k in keys})


@dataclass
class FluentElement:
    value: Any

    def to(self, a_type: Callable[[Any], ConvertedT]) -> ConvertedT:
        return a_type(self.value)

    def __str__(self) -> str:
        return str(self.value)


ConvertedT = TypeVar("ConvertedT")
