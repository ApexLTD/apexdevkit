from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Protocol, Self, Type, TypeVar
from warnings import warn

import httpx

from .fluent import JsonDict, JsonObject
from .url import HttpUrl

ResponseT = TypeVar("ResponseT", covariant=True)


class Http(Protocol[ResponseT]):  # pragma: no cover
    def with_header(self, key: str, value: str) -> Http[ResponseT]:
        pass

    def post(
        self, endpoint: str, json: dict[str, Any], headers: dict[str, Any] | None = None
    ) -> ResponseT:
        pass

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> ResponseT:
        pass

    def patch(self, endpoint: str, json: dict[str, Any]) -> ResponseT:
        pass

    def delete(self, endpoint: str) -> ResponseT:
        pass


@dataclass(frozen=True)
class FluentHttpx:
    http: Http[httpx.Response]

    def and_header(self, key: str, value: str) -> FluentHttpx:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> FluentHttpx:
        return FluentHttpx(self.http.with_header(key, value))

    def post(self) -> HttpxPost:
        return HttpxPost(self.http)

    def get(self) -> HttpxGet:
        return HttpxGet(self.http)

    def patch(self) -> HttpxPatch:
        return HttpxPatch(self.http)

    def delete(self) -> HttpxDelete:
        return HttpxDelete(self.http)


@dataclass(frozen=True)
class HttpxPost:
    http: Http[httpx.Response]

    json: JsonDict = field(default_factory=dict)

    def and_json(self, value: JsonDict) -> HttpxPost:  # pragma: no cover
        return self.with_json(value)

    def with_json(self, value: JsonDict) -> HttpxPost:
        return HttpxPost(self.http, json=value)

    def and_header(self, key: str, value: str) -> HttpxPost:  # pragma: no cover
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> HttpxPost:  # pragma: no cover
        warn(
            "Method 'HttpxPost.with_header' is deprecated, "
            "use 'FluentHttp.with_header' instead"
        )
        return HttpxPost(self.http.with_header(key, value))

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.post(value, json=self.json))


@dataclass(frozen=True)
class HttpxGet:
    http: Http[httpx.Response]

    params: dict[str, Any] = field(default_factory=dict)

    def with_params(self, **params: Any) -> HttpxGet:
        self.params.update(params)

        return self

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.get(value, params=self.params))


@dataclass(frozen=True)
class HttpxPatch:
    http: Http[httpx.Response]

    json: JsonDict = field(default_factory=dict)

    def with_json(self, value: JsonDict) -> HttpxPatch:
        return HttpxPatch(self.http, json=value)

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.patch(value, json=self.json))


@dataclass(frozen=True)
class HttpxDelete:
    http: Http[httpx.Response]

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.delete(value))


@dataclass(frozen=True)
class HttpxResponse:
    response: httpx.Response

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


@dataclass(frozen=True)
class Httpx:
    url: HttpUrl
    config: HttpxConfig

    @classmethod
    def create_for(cls, url: str) -> Self:
        return cls(HttpUrl(url), HttpxConfig())

    def with_header(self, key: str, value: str) -> Http[httpx.Response]:
        return Httpx(self.url, self.config.with_header(key, value))

    def post(
        self, endpoint: str, json: dict[str, Any], headers: dict[str, Any] | None = None
    ) -> httpx.Response:
        if headers:
            warn("Parameter 'headers' is deprecated, use '.with_header' before .post()")

        return httpx.post(
            self.url + endpoint, json=json, **self.config.add_headers(headers or {})
        )

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        return httpx.get(self.url + endpoint, params=params, **self.config)

    def patch(self, endpoint: str, json: dict[str, Any]) -> httpx.Response:
        return httpx.patch(self.url + endpoint, json=json, **self.config)

    def delete(self, endpoint: str) -> httpx.Response:
        return httpx.delete(self.url + endpoint, **self.config)


@dataclass(frozen=True)
class HttpxConfig(Mapping[str, Any]):
    timeout_s: int = 5
    headers: dict[str, str] = field(default_factory=dict)

    def with_header(self, key: str, value: str) -> HttpxConfig:
        self.headers[key] = value

        return self.add_headers({key: value})

    def with_user_agent(self, value: str) -> HttpxConfig:  # pragma: no cover
        warn(
            (
                """
                The 'with_user_agent(value)' method is deprecated.
                Please use 'with_header("user-agent", value)' instead.
                """
            )
        )

        return self.with_header(key="user-agent", value=value)

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeout": self.timeout_s,
            "headers": self.headers,
        }

    def add_headers(self, headers: dict[str, Any]) -> HttpxConfig:
        return HttpxConfig(
            timeout_s=self.timeout_s, headers={**self.headers, **headers}
        )

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
