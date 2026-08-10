from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from httpx2 import Client, Request, Response
from pypebbles import JsonDict

from apexdevkit.http.domain import HttpMethod, HttpRequest, HttpResponse
from apexdevkit.http.httpx.hooks import (
    AfterResponseHook,
    BeforeRequestHook,
    HttpxHandler,
)

_RequestHandler = HttpxHandler[Request]
_ResponseHandler = HttpxHandler[Response]


@dataclass
class HttpxBuilder:
    timeout_s: int = field(default_factory=lambda: 30)

    request_handlers: list[_RequestHandler] = field(default_factory=list)
    response_handlers: list[_ResponseHandler] = field(default_factory=list)

    url: str = field(init=False)

    def with_url(self, value: str) -> HttpxBuilder:
        self.url = value

        return self

    def with_timeout(self, timeout_s: int) -> HttpxBuilder:
        self.timeout_s = timeout_s

        return self

    def before_request(self, handler: _RequestHandler) -> HttpxBuilder:
        self.request_handlers.append(handler)

        return self

    def after_response(self, handler: _ResponseHandler) -> HttpxBuilder:
        self.response_handlers.append(handler)

        return self

    def build(self) -> Httpx:
        return Httpx(self._build_client())

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
class HttpxChannel:
    client: Client

    def transport(self, request: HttpRequest) -> HttpxTransporter:
        return HttpxTransporter(client=self.client, request=request)


@dataclass(frozen=True)
class HttpxTransporter:
    client: Client
    request: HttpRequest

    def over(self, method: HttpMethod) -> HttpResponse:
        return _HttpxResponse(
            self.client.request(
                method=method.name,
                url=self.request.endpoint,
                headers=self.request.headers,
                params=self.request.params,
                json=self.request.json,
                data=self.request.data,
            )
        )


@dataclass(frozen=True)
class Httpx:
    client: Client

    _request: HttpRequest = field(default_factory=HttpRequest)

    Builder = HttpxBuilder

    def with_endpoint(self, value: str) -> Httpx:
        return replace(self, _request=self._request.with_endpoint(value))

    def with_header(self, key: str, value: str) -> Httpx:
        return replace(self, _request=self._request.with_header(key, value))

    def with_param(self, key: str, value: str) -> Httpx:
        return replace(self, _request=self._request.with_param(key, value))

    def with_data(self, value: Any) -> Httpx:
        return replace(self, _request=self._request.with_data(value))

    def with_json(self, value: JsonDict) -> Httpx:
        return replace(self, _request=self._request.with_json(value))

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        return (
            HttpxChannel(self.client)
            .transport(self._request.with_endpoint(endpoint))
            .over(method)
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

    def to[T](self, a_type: Callable[[_HttpxResponse], T]) -> T:
        return a_type(self)
