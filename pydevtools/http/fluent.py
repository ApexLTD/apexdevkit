from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterator, Protocol, Self, Type, TypeVar


class FluentHttp(Protocol):  # pragma: no cover
    def post(self) -> FluentHttpPost:
        pass

    def get(self) -> FluentHttpGet:
        pass


class FluentHttpPost(Protocol):  # pragma: no cover
    def with_json(self, value: JsonDict) -> Self:
        pass

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        pass


JsonDict = dict[str, Any]


class FluentHttpGet(Protocol):  # pragma: no cover
    def on_endpoint(self, value: str) -> FluentHttpResponse:
        pass


class FluentHttpResponse(Protocol):  # pragma: no cover
    def on_bad_request(self, raises: Exception | Type[Exception]) -> Self:
        pass

    def on_failure(self, raises: Type[Exception]) -> Self:
        pass

    def json(self) -> JsonObject[Any]:
        pass


ValueT = TypeVar("ValueT")


@dataclass
class JsonObject(Generic[ValueT]):
    raw: dict[str, ValueT]

    def __iter__(self) -> Iterator[tuple[str, ValueT]]:
        yield from self.raw.items()

    def select(self, *keys: str) -> JsonObject[ValueT]:
        return JsonObject({k: v for k, v in self.raw.items() if k in keys})

    def value_of(self, key: str) -> JsonElement[ValueT]:
        return JsonElement(self.raw[key])

    def drop(self, *keys: str) -> JsonObject[ValueT]:
        return JsonObject({k: v for k, v in self.raw.items() if k not in keys})


@dataclass
class JsonList(Generic[ValueT]):
    raw: list[dict[str, ValueT]]

    def __iter__(self) -> Iterator[dict[str, ValueT]]:
        yield from self.raw


ConvertedT = TypeVar("ConvertedT")


@dataclass
class JsonElement(Generic[ValueT]):
    value: ValueT

    def to(self, a_type: Callable[[ValueT], ConvertedT]) -> ConvertedT:
        return a_type(self.value)
