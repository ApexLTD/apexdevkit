from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx

from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.httpx.hooks import (
    AfterResponseHook,
    BeforeRequestHook,
    HttpxHandler,
)
from apexdevkit.http.json import JsonDict
from apexdevkit.http.url import HttpUrl

_RequestHandler = HttpxHandler[httpx.Request]
_ResponseHandler = HttpxHandler[httpx.Response]


def default_config() -> HttpxConfig:
    return HttpxConfig()


@dataclass(frozen=True)
class Httpx:
    client: httpx.Client

    config: HttpxConfig = field(default_factory=default_config)

    def with_endpoint(self, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_endpoint(value))

    def with_header(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_header(key, value))

    def with_param(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self.config.with_param(key, value))

    def with_data(self, value: Any) -> Httpx:
        return Httpx(self.client, self.config.with_data(value))

    def with_json(self, value: JsonDict) -> Httpx:
        return Httpx(self.client, self.config.with_json(value))

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        return _HttpxResponse(
            self.client.request(
                method.name,
                **self.config.with_endpoint(endpoint),
            )
        )

    @dataclass
    class Builder:
        timeout_s: int = field(default_factory=lambda: 30)
        config: HttpxConfig = field(default_factory=default_config)

        request_handlers: list[_RequestHandler] = field(default_factory=list)
        response_handlers: list[_ResponseHandler] = field(default_factory=list)

        url: str = field(init=False)

        def with_url(self, value: str) -> Httpx.Builder:
            self.url = value

            return self

        def with_timeout(self, timeout_s: int) -> Httpx.Builder:
            self.timeout_s = timeout_s

            return self

        def and_config(self, value: HttpxConfig) -> Httpx.Builder:
            self.config = value

            return self

        def before_request(self, handler: _RequestHandler) -> Httpx.Builder:
            self.request_handlers.append(handler)

            return self

        def after_response(self, handler: _ResponseHandler) -> Httpx.Builder:
            self.response_handlers.append(handler)

            return self

        def build(self) -> Httpx:
            return Httpx(self._build_client(), self.config)

        def _build_client(self) -> httpx.Client:
            return httpx.Client(
                base_url=self.url,
                timeout=self.timeout_s,
                event_hooks={
                    "request": self._build_before_request_hooks(),
                    "response": self._build_after_response_hooks(),
                },
            )

        def _build_before_request_hooks(self) -> list[Callable[..., Any]]:
            return [BeforeRequestHook(handler) for handler in self.request_handlers]

        def _build_after_response_hooks(self) -> list[Callable[..., Any]]:
            return [AfterResponseHook(handler) for handler in self.response_handlers]


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
    data: Any | None = None

    def with_endpoint(self, endpoint: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=HttpUrl(self.endpoint) + endpoint,
            headers=self.headers,
            params=self.params,
            json=self.json,
            data=self.data,
        )

    def with_header(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers.merge(JsonDict({key: value})),
            params=self.params,
            json=self.json,
            data=self.data,
        )

    def with_param(self, key: str, value: str) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers,
            params=self.params.merge(JsonDict({key: value})),
            json=self.json,
            data=self.data,
        )

    def with_data(self, value: Any) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers,
            params=self.params,
            json=self.json,
            data=value,
        )

    def with_json(self, value: JsonDict) -> HttpxConfig:
        return HttpxConfig(
            endpoint=self.endpoint,
            headers=self.headers,
            params=self.params,
            json=value,
            data=self.data,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.endpoint,
            "headers": dict(self.headers),
            "params": dict(self.params),
            "json": dict(self.json) if self.json is not None else None,
            "data": self._data() if self.data is not None else None,
        }

    def _data(self) -> Any:
        if isinstance(self.data, Mapping):
            return dict(self.data)
        return str(self.data)

    def __len__(self) -> int:
        return len(self.as_dict())

    def __iter__(self) -> Iterator[str]:
        return iter(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict().__getitem__(key)
