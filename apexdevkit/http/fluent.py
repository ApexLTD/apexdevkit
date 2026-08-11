from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from pypebbles import JsonDict

from .domain import HttpMethod, HttpRequest, HttpResponse, HttpTransport


@dataclass(frozen=True)
class FluentHttp:
    transporter: HttpTransport

    _request: HttpRequest = field(default_factory=HttpRequest)

    def on_endpoint(self, value: str) -> HttpRequestDispatcher:
        return HttpRequestDispatcher(
            transporter=self.transporter,
            inner=self._request.with_endpoint(value),
        )

    def and_header(self, key: str, value: str) -> FluentHttp:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> FluentHttp:
        return replace(self, _request=self._request.with_header(key, value))

    def and_param(self, key: str, value: str) -> FluentHttp:
        return self.with_param(key, value)

    def with_param(self, key: str, value: str) -> FluentHttp:
        return replace(self, _request=self._request.with_param(key, value))

    def and_json(self, value: JsonDict) -> FluentHttp:
        return self.with_json(value)  # pragma: no cover

    def with_json(self, value: JsonDict) -> FluentHttp:
        return replace(self, _request=self._request.with_json(value))

    def and_data(self, value: Any) -> FluentHttp:
        return self.with_data(value)  # pragma: no cover

    def with_data(self, value: Any) -> FluentHttp:
        return replace(self, _request=self._request.with_data(value))


@dataclass(frozen=True)
class HttpRequestDispatcher:
    inner: HttpRequest
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
        return self.transporter.over(method).transport(self.inner)
