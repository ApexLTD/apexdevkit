from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Protocol

from pypebbles import FluentDict, JsonDict

from apexdevkit.http.url import HttpUrl

from .method import HttpMethod
from .response import HttpResponse


@dataclass(frozen=True)
class HttpRequest:
    endpoint: str = ""
    headers: FluentDict[str] = field(default_factory=FluentDict[str])
    params: FluentDict[str] = field(default_factory=FluentDict[str])
    json: JsonDict | None = None
    data: JsonDict | None = None

    def with_endpoint(self, endpoint: str) -> HttpRequest:
        return replace(self, endpoint=HttpUrl(self.endpoint) + endpoint)

    def with_header(self, key: str, value: str) -> HttpRequest:
        return self.with_headers({key: value})

    def with_headers(self, value: Mapping[str, str]) -> HttpRequest:
        return replace(self, headers=self.headers.merge(FluentDict[str](value)))

    def with_param(self, key: str, value: str) -> HttpRequest:
        return self.with_params({key: value})

    def with_params(self, value: Mapping[str, str]) -> HttpRequest:
        return replace(self, params=self.params.merge(FluentDict[str](value)))

    def with_data(self, value: JsonDict) -> HttpRequest:
        return replace(self, data=value)

    def with_json(self, value: JsonDict) -> HttpRequest:
        return replace(self, json=value)

    def using(self, transporter: HttpTransport) -> HttpDispatcher:
        return HttpDispatcher(request=self, transporter=transporter)


@dataclass(frozen=True)
class HttpDispatcher:
    request: HttpRequest
    transporter: HttpTransport

    def post(self) -> HttpResponse:
        return self.dispatch(HttpMethod.post)

    def get(self) -> HttpResponse:
        return self.dispatch(HttpMethod.get)

    def patch(self) -> HttpResponse:
        return self.dispatch(HttpMethod.patch)

    def delete(self) -> HttpResponse:
        return self.dispatch(HttpMethod.delete)

    def put(self) -> HttpResponse:
        return self.dispatch(HttpMethod.put)

    def dispatch(self, method: HttpMethod) -> HttpResponse:
        return self.transporter.over(method).transport(self.request)


class HttpTransport(Protocol):
    def __call__(self, method: HttpMethod) -> HttpTransport:
        pass

    def over(self, method: HttpMethod) -> HttpTransport:
        pass

    def transport(self, request: HttpRequest) -> HttpResponse:
        pass
