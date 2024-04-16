from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Self, Type

import httpx

from .fluent import JsonDict, JsonObject
from .url import HttpUrl


@dataclass(frozen=True)
class FluentHttpx:
    http: Httpx

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
    http: Httpx

    json: JsonDict = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)

    def with_json(self, value: JsonDict) -> HttpxPost:
        return HttpxPost(self.http, json=value)

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(
            self.http.post(value, json=self.json, headers=self.headers)
        )

    def and_header(self, key: str, value: str) -> HttpxPost:
        self.headers[key] = value

        return self


@dataclass(frozen=True)
class HttpxGet:
    http: Httpx
    params: dict[str, Any] = field(default_factory=dict)

    def with_params(self, **params: Any) -> HttpxGet:
        self.params.update(params)

        return self

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.get(value, params=self.params))


@dataclass(frozen=True)
class HttpxPatch:
    http: Httpx

    json: JsonDict = field(default_factory=dict)

    def with_json(self, value: JsonDict) -> HttpxPatch:
        return HttpxPatch(self.http, json=value)

    def on_endpoint(self, value: str) -> HttpxResponse:
        return HttpxResponse(self.http.patch(value, json=self.json))


@dataclass(frozen=True)
class HttpxDelete:
    http: Httpx

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
        try:
            self.response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise raises(e.response.content)

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

    def post(
        self, endpoint: str, json: dict[str, Any], headers: dict[str, Any]
    ) -> httpx.Response:
        return httpx.post(
            self.url + endpoint, json=json, **self.config.add_headers(headers)
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

    def with_header(self, key: str, value: str) -> Self:
        self.headers[key] = value

        return self

    def with_user_agent(self, value: str) -> Self:
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
