from __future__ import annotations

from dataclasses import dataclass, field, replace

from httpx2 import Client, Request, Response
from pypebbles import FluentDict

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

    def channel(self) -> HttpxChannel:
        return HttpxChannel(client=self.client())

    def client(self) -> Client:
        return Client(
            base_url=self.url,
            timeout=self.timeout_s,
            event_hooks={
                "request": [BeforeRequestHook(h) for h in self.request_handlers],
                "response": [AfterResponseHook(h) for h in self.response_handlers],
            },
        )


@dataclass(frozen=True)
class HttpxChannel:
    client: Client

    headers: FluentDict[str] = field(default_factory=FluentDict[str])

    def with_header(self, key: str, value: str) -> HttpxChannel:
        return replace(self, headers=self.headers.merge(FluentDict[str]({key: value})))

    def transport(self, request: HttpRequest) -> HttpxTransport:
        return HttpxTransport(
            client=self.client,
            request=request.with_headers(self.headers),
        )


@dataclass(frozen=True)
class HttpxTransport:
    client: Client
    request: HttpRequest

    def over(self, method: HttpMethod) -> HttpResponse:
        return self.parse(
            self.client.request(
                method=method.name,
                url=self.request.endpoint,
                headers=self.request.headers,
                params=self.request.params,
                json=self.request.json,
                data=self.request.data,
            )
        )

    @staticmethod
    def parse(response: Response) -> HttpResponse:
        return HttpResponse(
            status=response.status_code,
            content=response.content,
        )
