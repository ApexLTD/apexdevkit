from __future__ import annotations

from dataclasses import dataclass, field, replace

from httpx2 import Client, Request, Response
from pypebbles import FluentDict

from apexdevkit.http import FluentHttp
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

    headers: FluentDict[str] = field(default_factory=FluentDict[str])

    def with_header(self, key: str, value: str) -> HttpxBuilder:
        self.headers.merge(FluentDict[str]({key: value}))

        return self

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

    def build(self) -> FluentHttp:
        return FluentHttp(self.transport())

    def transport(self) -> HttpxTransporter:
        return HttpxTransporter(self.client())

    def client(self) -> Client:
        return Client(
            base_url=self.url,
            timeout=self.timeout_s,
            headers=self.headers,
            event_hooks={
                "request": [BeforeRequestHook(h) for h in self.request_handlers],
                "response": [AfterResponseHook(h) for h in self.response_handlers],
            },
        )


@dataclass(frozen=True)
class HttpxTransporter:
    client: Client

    method: HttpMethod = HttpMethod.get

    def __call__(self, method: HttpMethod) -> HttpxTransporter:
        return self.over(method)

    def over(self, method: HttpMethod) -> HttpxTransporter:
        return replace(self, method=method)

    def transport(self, request: HttpRequest) -> HttpResponse:
        return self.parse(
            self.client.request(
                method=self.method.name,
                url=request.endpoint,
                headers=request.headers,
                params=request.params,
                json=request.json,
                data=request.data,
            )
        )

    @staticmethod
    def parse(response: Response) -> HttpResponse:
        return HttpResponse(
            status=response.status_code,
            content=response.content,
        )
