from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Self

import httpx

from pydevtools.http.fluent import HttpResponse
from pydevtools.http.json import JsonDict
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

    def with_param(self, key: str, value: str) -> Httpx:
        return Httpx(self.url, self.config.with_param(key, value))

    def post(self, endpoint: str, json: JsonDict) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.post(
                self.url + endpoint,
                headers=self.config["headers"],
                json=dict(json),
            )
        )

    def get(self, endpoint: str) -> HttpResponse:
        return HttpxResponseAdapter(
            httpx.get(
                self.url + endpoint,
                params=self.config["params"],
            )
        )

    def patch(self, endpoint: str, json: JsonDict) -> HttpResponse:
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

    def json(self) -> JsonDict:
        return JsonDict(self.inner.json())


@dataclass(frozen=True)
class HttpxConfig(Mapping[str, Any]):
    timeout_s: int = 30
    headers: JsonDict = field(default_factory=JsonDict)
    params: JsonDict = field(default_factory=JsonDict)

    def and_header(self, key: str, value: str) -> HttpxConfig:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            timeout_s=self.timeout_s,
            headers=self.headers.merge(JsonDict({key: value})),
            params=self.params,
        )

    def with_param(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            timeout_s=self.timeout_s,
            headers=self.headers,
            params=self.params.merge(JsonDict({key: value})),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeout": self.timeout_s,
            "headers": dict(self.headers),
            "params": dict(self.params),
        }

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
