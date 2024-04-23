from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Iterator, TypeVar

ValueT = TypeVar("ValueT")


@dataclass
class JsonObject(Generic[ValueT]):
    raw: dict[str, ValueT] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.raw)

    def __iter__(self) -> Iterator[tuple[str, ValueT]]:
        yield from self.raw.items()

    def with_a(self, **fields: ValueT) -> JsonObject[ValueT]:
        return JsonObject({**self.raw, **fields})

    def select(self, *keys: str) -> JsonObject[ValueT]:
        return JsonObject({k: v for k, v in self.raw.items() if k in keys})

    def value_of(self, key: str) -> JsonElement[ValueT]:
        return JsonElement(self.raw[key])

    def drop(self, *keys: str) -> JsonObject[ValueT]:
        return self.select(*set(self.raw.keys()).difference(keys))

    def merge(self, other: JsonObject[ValueT]) -> JsonObject[ValueT]:
        return JsonObject({**self.raw, **other.raw})


@dataclass
class JsonList(Generic[ValueT]):
    raw: list[JsonObject[ValueT]]

    def __iter__(self) -> Iterator[JsonObject[ValueT]]:
        yield from self.raw


ConvertedT = TypeVar("ConvertedT")


@dataclass
class JsonElement(Generic[ValueT]):
    value: ValueT

    def to(self, a_type: Callable[[ValueT], ConvertedT]) -> ConvertedT:
        return a_type(self.value)

    def __str__(self) -> str:
        return str(self.value)
