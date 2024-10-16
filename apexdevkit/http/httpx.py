from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Self

import httpx
from httpx import Client

from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.json import JsonDict
from apexdevkit.http.url import HttpUrl


def default_config() -> HttpxConfig:
    return HttpxConfig()


@dataclass(frozen=True)
class Httpx:
    client: httpx.Client

    config: HttpxConfig = field(default_factory=default_config)

    @classmethod
    def create_for(cls, url: str) -> Self:
        return cls(Client(base_url=url))

    def with_endpoint(self, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_endpoint(value))

    def with_header(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_header(key, value))

    def with_param(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_param(key, value))

    def with_json(self, value: JsonDict) -> Httpx:
        return Httpx(self.client, self.config.with_json(value))

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        return _HttpxResponse(
            self.client.request(
                method.name,
                **self.config.with_endpoint(endpoint),
            )
        )


@dataclass(frozen=True)
class _HttpxResponse:
    inner: httpx.Response

    def code(self) -> int:
        return self.inner.status_code

    def raw(self) -> bytes:
        return self.inner.content

    def json(self) -> JsonDict:
        return JsonDict(self.inner.json())


@dataclass(frozen=True)
class HttpxConfig(Mapping[str, Any]):
    endpoint: str = ""
    headers: JsonDict = field(default_factory=JsonDict)
    params: JsonDict = field(default_factory=JsonDict)
    json: JsonDict | None = None

    def with_endpoint(self, endpoint: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=HttpUrl(self.endpoint) + endpoint,
            headers=self.headers,
            params=self.params,
            json=self.json,
        )

    def with_header(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers.merge(JsonDict({key: value})),
            params=self.params,
            json=self.json,
        )

    def with_param(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers,
            params=self.params.merge(JsonDict({key: value})),
            json=self.json,
        )

    def with_json(self, value: JsonDict) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers,
            params=self.params,
            json=value,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.endpoint,
            "headers": dict(self.headers),
            "params": dict(self.params),
            "json": dict(self.json) if self.json is not None else None,
        }

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
