from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from httpx2 import Client, Request, Response
from pypebbles import JsonDict

from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.httpx.hooks import (
    AfterResponseHook,
    BeforeRequestHook,
    HttpxHandler,
)
from apexdevkit.http.url import HttpUrl

_RequestHandler = HttpxHandler[Request]
_ResponseHandler = HttpxHandler[Response]


@dataclass
class HttpxBuilder:
    timeout_s: int = field(default_factory=lambda: 30)
    config: HttpxRequest = field(default_factory=lambda: HttpxRequest())

    request_handlers: list[_RequestHandler] = field(default_factory=list)
    response_handlers: list[_ResponseHandler] = field(default_factory=list)

    url: str = field(init=False)

    def with_url(self, value: str) -> HttpxBuilder:
        self.url = value

        return self

    def with_timeout(self, timeout_s: int) -> HttpxBuilder:
        self.timeout_s = timeout_s

        return self

    def and_config(self, value: HttpxRequest) -> HttpxBuilder:
        self.config = value

        return self

    def before_request(self, handler: _RequestHandler) -> HttpxBuilder:
        self.request_handlers.append(handler)

        return self

    def after_response(self, handler: _ResponseHandler) -> HttpxBuilder:
        self.response_handlers.append(handler)

        return self

    def build(self) -> Httpx:
        return Httpx(self._build_client(), self.config)

    def _build_client(self) -> Client:
        return Client(
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
class Httpx:
    client: Client

    _request: HttpxRequest = field(default_factory=lambda: HttpxRequest())

    Builder = HttpxBuilder

    def with_endpoint(self, value: str) -> Httpx:
        return Httpx(self.client, self._request.with_endpoint(value))

    def with_header(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self._request.with_header(key, value))

    def with_param(self, key: str, value: str) -> Httpx:
        return Httpx(self.client, self._request.with_param(key, value))

    def with_data(self, value: Any) -> Httpx:
        return Httpx(self.client, self._request.with_data(value))

    def with_json(self, value: JsonDict) -> Httpx:
        return Httpx(self.client, self._request.with_json(value))

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        return _HttpxResponse(
            self._request.with_endpoint(endpoint).send(method, using=self.client)
        )


@dataclass(frozen=True)
class _HttpxResponse:
    inner: Response

    def code(self) -> int:
        return self.inner.status_code

    def raw(self) -> bytes:
        return self.inner.content

    def json(self) -> JsonDict:
        return JsonDict(self.inner.json())


@dataclass(frozen=True)
class HttpxRequest:
    endpoint: str = ""
    headers: JsonDict = field(default_factory=JsonDict)
    params: JsonDict = field(default_factory=JsonDict)
    json: JsonDict | None = None
    data: JsonDict | None = None

    def with_endpoint(self, endpoint: str) -> HttpxRequest:
        return replace(self, endpoint=HttpUrl(self.endpoint) + endpoint)

    def with_header(self, key: str, value: str) -> HttpxRequest:
        return replace(self, headers=self.headers.merge(JsonDict({key: value})))

    def with_param(self, key: str, value: str) -> HttpxRequest:
        return replace(self, params=self.params.merge(JsonDict({key: value})))

    def with_data(self, value: JsonDict) -> HttpxRequest:
        return replace(self, data=value)

    def with_json(self, value: JsonDict) -> HttpxRequest:
        return replace(self, json=value)

    def send(self, method: HttpMethod, using: Client) -> Response:
        return using.request(
            method.name,
            url=self.endpoint,
            headers=self.headers,
            params=self.params,
            json=self.json if self.json is not None else None,
            data=self.data if self.data is not None else None,
        )
