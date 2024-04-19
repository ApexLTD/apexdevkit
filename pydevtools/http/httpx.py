from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Iterator, Mapping, Protocol, Self, Type, TypeVar

import httpx

from ..annotation import deprecated
from .fluent import JsonDict, JsonObject
from .url import HttpUrl

ResponseT = TypeVar("ResponseT", covariant=True)


class Http(Protocol[ResponseT]):  # pragma: no cover
    def with_header(self, key: str, value: str) -> Http[ResponseT]:
        pass

    def post(self, endpoint: str, json: dict[str, Any]) -> ResponseT:
        pass

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> ResponseT:
        pass

    def patch(self, endpoint: str, json: dict[str, Any]) -> ResponseT:
        pass

    def delete(self, endpoint: str) -> ResponseT:
        pass


@dataclass(frozen=True)
class FluentHttp(Generic[ResponseT]):
    http: Http[ResponseT]

    def and_header(self, key: str, value: str) -> FluentHttp[ResponseT]:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> FluentHttp[ResponseT]:
        return FluentHttp(self.http.with_header(key, value))

    def post(self) -> HttpxPost[ResponseT]:
        return HttpxPost(self.http)

    def get(self) -> HttpxGet[ResponseT]:
        return HttpxGet(self.http)

    def patch(self) -> HttpxPatch[ResponseT]:
        return HttpxPatch(self.http)

    def delete(self) -> HttpxDelete[ResponseT]:
        return HttpxDelete(self.http)


@dataclass(frozen=True)
class HttpxPost(Generic[ResponseT]):
    http: Http[ResponseT]

    json: JsonDict = field(default_factory=dict)

    def and_json(self, value: JsonDict) -> HttpxPost[ResponseT]:  # pragma: no cover
        return self.with_json(value)

    def with_json(self, value: JsonDict) -> HttpxPost[ResponseT]:
        return HttpxPost(self.http, json=value)

    def on_endpoint(self, value: str) -> ResponseT:
        return self.http.post(value, json=self.json)


@dataclass(frozen=True)
class HttpxGet(Generic[ResponseT]):
    http: Http[ResponseT]

    params: dict[str, Any] = field(default_factory=dict)

    def with_params(self, **params: Any) -> HttpxGet[ResponseT]:
        self.params.update(params)

        return self

    def on_endpoint(self, value: str) -> ResponseT:
        return self.http.get(value, params=self.params)


@dataclass(frozen=True)
class HttpxPatch(Generic[ResponseT]):
    http: Http[ResponseT]

    json: JsonDict = field(default_factory=dict)

    def with_json(self, value: JsonDict) -> HttpxPatch[ResponseT]:
        return HttpxPatch(self.http, json=value)

    def on_endpoint(self, value: str) -> ResponseT:
        return self.http.patch(value, json=self.json)


@dataclass(frozen=True)
class HttpxDelete(Generic[ResponseT]):
    http: Http[ResponseT]

    def on_endpoint(self, value: str) -> ResponseT:
        return self.http.delete(value)


@dataclass(frozen=True)
class HttpxResponse:
    response: HttpResponse

    def on_bad_request(self, raises: Exception | Type[Exception]) -> Self:
        if self.response.status_code == 400:
            raise raises

        return self

    def on_failure(self, raises: Type[Exception]) -> Self:
        if self.response.status_code < 200 or self.response.status_code > 299:
            raise raises(self.response.content)

        return self

    def json(self) -> JsonObject[Any]:
        return JsonObject(self.response.json())

    def on_conflict(self, raises: Exception | Type[Exception]) -> Self:
        if self.response.status_code == 409:
            raise raises

        return self


class HttpResponse(Protocol):
    status_code: int

    @property
    def content(self) -> Any:
        pass

    def json(self) -> dict[str, Any]:
        pass


@dataclass(frozen=True)
class Httpx:
    url: HttpUrl
    config: HttpxConfig

    @classmethod
    def create_for(cls, url: str) -> Self:
        return cls(HttpUrl(url), HttpxConfig())

    def with_header(self, key: str, value: str) -> Http[HttpxResponse]:
        return Httpx(self.url, self.config.with_header(key, value))

    def post(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        return self._load(httpx.post(self.url + endpoint, json=json, **self.config))

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> HttpxResponse:
        return self._load(httpx.get(self.url + endpoint, params=params, **self.config))

    def patch(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        return self._load(httpx.patch(self.url + endpoint, json=json, **self.config))

    def delete(self, endpoint: str) -> HttpxResponse:
        return self._load(httpx.delete(self.url + endpoint, **self.config))

    def _load(self, response: httpx.Response) -> HttpxResponse:
        return HttpxResponse(response)


@deprecated("Class HttpxAdapter is deprecated, use Httpx instead")
@dataclass(frozen=True)
class HttpxAdapter:  # pragma: no cover
    http: Http[HttpxResponse]

    def with_header(self, key: str, value: str) -> Http[HttpxResponse]:
        return HttpxAdapter(self.http.with_header(key, value))

    def post(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        return self.http.post(endpoint, json=json)

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> HttpxResponse:
        return self.http.get(endpoint, params=params)

    def patch(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        return self.http.patch(endpoint, json=json)

    def delete(self, endpoint: str) -> HttpxResponse:
        return self.http.delete(endpoint)


@dataclass(frozen=True)
class HttpxConfig(Mapping[str, Any]):
    timeout_s: int = 5
    headers: Mapping[str, str] = field(default_factory=dict)

    def with_header(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            timeout_s=self.timeout_s,
            headers={**self.headers, key: value},
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeout": self.timeout_s,
            "headers": self.headers,
        }

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
