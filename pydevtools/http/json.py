from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterator, TypeVar

from pydevtools.annotation import deprecated


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


ValueT = TypeVar("ValueT")


@dataclass
class JsonObject(Generic[ValueT]):
    raw: dict[str, ValueT] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.raw)

    def __iter__(self) -> Iterator[tuple[str, ValueT]]:
        yield from self.raw.items()

    @deprecated("JsonObject is deprecated, use JsonDict instead")
    def with_a(self, **fields: ValueT) -> JsonObject[ValueT]:
        return JsonObject({**self.raw, **fields})

    @deprecated("JsonObject is deprecated, use JsonDict instead")
    def select(self, *keys: str) -> JsonObject[ValueT]:
        return JsonObject({k: v for k, v in self.raw.items() if k in keys})

    @deprecated("JsonObject is deprecated, use JsonDict instead")
    def value_of(self, key: str) -> JsonElement[ValueT]:
        return JsonElement(self.raw[key])

    @deprecated("JsonObject is deprecated, use JsonDict instead")
    def drop(self, *keys: str) -> JsonObject[ValueT]:
        return self.select(*set(self.raw.keys()).difference(keys))

    @deprecated("JsonObject is deprecated, use JsonDict instead")
    def merge(self, other: JsonObject[ValueT]) -> JsonObject[ValueT]:
        return JsonObject({**self.raw, **other.raw})


@dataclass
class JsonList(Generic[ValueT]):
    raw: list[JsonDict]

    def __iter__(self) -> Iterator[JsonDict]:
        yield from self.raw


ConvertedT = TypeVar("ConvertedT")


@dataclass
class JsonElement(Generic[ValueT]):
    value: ValueT

    @deprecated("JsonElement is deprecated, use FluentItem instead")
    def to(self, a_type: Callable[[ValueT], ConvertedT]) -> ConvertedT:
        return a_type(self.value)

    def __str__(self) -> str:
        return str(self.value)
