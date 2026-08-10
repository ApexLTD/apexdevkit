from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Protocol

from pypebbles import JsonDict

from .domain import HttpChannel, HttpMethod, HttpRequest, HttpResponse


class Http(Protocol):  # pragma: no cover
    def with_endpoint(self, value: str) -> Http:
        pass

    def with_header(self, key: str, value: str) -> Http:
        pass

    def with_param(self, key: str, value: str) -> Http:
        pass

    def with_json(self, value: JsonDict) -> Http:
        pass

    def with_data(self, value: Any) -> Http:
        pass

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        pass


@dataclass(frozen=True)
class _WorkaroundChannel:
    http: Http

    _request: HttpRequest = field(default_factory=HttpRequest)

    def transport(self, request: HttpRequest) -> _WorkaroundChannel:
        return replace(self, _request=request)

    def over(self, method: HttpMethod) -> HttpResponse:
        return self.http.request(method, endpoint=self._request.endpoint)


@dataclass(frozen=True)
class FluentHttp:
    http: Http

    _request: HttpRequest = field(default_factory=HttpRequest)

    def on_endpoint(self, value: str) -> FluentHttpRequest:
        return FluentHttpRequest(
            channel=_WorkaroundChannel(self.http),
            inner=self._request.with_endpoint(value),
        )

    def and_header(self, key: str, value: str) -> FluentHttp:
        return self.with_header(key, value)

    def with_header(self, key: str, value: str) -> FluentHttp:
        return FluentHttp(self.http.with_header(key, value))

    def and_param(self, key: str, value: str) -> FluentHttp:
        return self.with_param(key, value)

    def with_param(self, key: str, value: str) -> FluentHttp:
        return FluentHttp(self.http.with_param(key, value))

    def and_json(self, value: JsonDict) -> FluentHttp:
        return self.with_json(value)  # pragma: no cover

    def with_json(self, value: JsonDict) -> FluentHttp:
        return FluentHttp(self.http.with_json(value))

    def and_data(self, value: Any) -> FluentHttp:
        return self.with_data(value)  # pragma: no cover

    def with_data(self, value: Any) -> FluentHttp:
        return FluentHttp(self.http.with_data(value))


@dataclass(frozen=True)
class FluentHttpRequest:
    inner: HttpRequest
    channel: HttpChannel

    def post(self) -> FluentHttpResponse:
        return self.request(HttpMethod.post)

    def get(self) -> FluentHttpResponse:
        return self.request(HttpMethod.get)

    def patch(self) -> FluentHttpResponse:
        return self.request(HttpMethod.patch)

    def delete(self) -> FluentHttpResponse:
        return self.request(HttpMethod.delete)

    def put(self) -> FluentHttpResponse:
        return self.request(HttpMethod.put)

    def request(self, method: HttpMethod) -> FluentHttpResponse:
        return self.channel.transport(self.inner).over(method).to(FluentHttpResponse)


@dataclass(frozen=True)
class FluentHttpResponse:
    response: HttpResponse

    def on_bad_request(self, raises: Exception | type[Exception]) -> FluentHttpResponse:
        if self.response.code() == 400:
            raise raises

        return self

    def on_conflict(self, raises: Exception | type[Exception]) -> FluentHttpResponse:
        if self.response.code() == 409:
            raise raises

        return self

    def on_not_found(self, raises: Exception | type[Exception]) -> FluentHttpResponse:
        if self.response.code() == 404:
            raise raises

        return self

    def on_failure(self, raises: type[Exception]) -> FluentHttpResponse:
        if self.response.code() < 200 or self.response.code() > 299:
            raise raises(self.response.raw(), self.response.code())

        return self

    def json(self) -> JsonDict:
        return self.response.json()
