from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Self

import httpx

from pydevtools.http.fluent import HttpResponse
from pydevtools.http.json import JsonObject
from pydevtools.http.url import HttpUrl


@dataclass(frozen=True)
class Httpx:
    url: HttpUrl
    config: HttpxConfig

    @classmethod
    def create_for(cls, url: str) -> Self:
        return cls(HttpUrl(url), HttpxConfig())

    def with_header(self, key: str, value: str) -> Httpx:
        return Httpx(self.url, self.config.with_header(key, value))

    def post(self, endpoint: str, json: JsonObject[Any]) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.post(
                self.url + endpoint,
                json=dict(json),
                **self.config,
            )
        )

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.get(
                self.url + endpoint,
                params=params,
                **self.config,
            )
        )

    def patch(self, endpoint: str, json: JsonObject[Any]) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.patch(
                self.url + endpoint,
                json=dict(json),
                **self.config,
            )
        )

    def delete(self, endpoint: str) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.delete(
                self.url + endpoint,
                **self.config,
            )
        )


@dataclass
class HttpxResponseAdapter:
    inner: httpx.Response

    def code(self) -> int:
        return self.inner.status_code

    def raw(self) -> bytes:
        return self.inner.content

    def json(self) -> JsonObject[Any]:
        return JsonObject(self.inner.json())


@dataclass(frozen=True)
class HttpxConfig(Mapping[str, Any]):
    timeout_s: int = 30
    headers: JsonObject[str] = field(default_factory=JsonObject[str])

    def and_header(self, key: str, value: str) -> HttpxConfig:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            timeout_s=self.timeout_s,
            headers=self.headers.with_a(**{key: value}),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeout": self.timeout_s,
            "headers": dict(self.headers),
        }

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
