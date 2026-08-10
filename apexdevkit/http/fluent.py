from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from pypebbles import JsonDict

from .domain import HttpChannel, HttpMethod, HttpRequest, HttpResponse


@dataclass(frozen=True)
class FluentHttp:
    channel: HttpChannel

    _request: HttpRequest = field(default_factory=HttpRequest)

    def on_endpoint(self, value: str) -> FluentHttpRequest:
        return FluentHttpRequest(
            channel=self.channel,
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
class FluentHttpRequest:
    inner: HttpRequest
    channel: HttpChannel

    def post(self) -> HttpResponse:
        return self.request(HttpMethod.post)

    def get(self) -> HttpResponse:
        return self.request(HttpMethod.get)

    def patch(self) -> HttpResponse:
        return self.request(HttpMethod.patch)

    def delete(self) -> HttpResponse:
        return self.request(HttpMethod.delete)

    def put(self) -> HttpResponse:
        return self.request(HttpMethod.put)

    def request(self, method: HttpMethod) -> HttpResponse:
        return self.channel.transport(self.inner).over(method)
