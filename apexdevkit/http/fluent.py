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
        return self.http.request(method)


@dataclass(frozen=True)
class FluentHttp:
    http: Http

    def on_endpoint(self, value: str) -> _RequestAlt:
        return _RequestAlt(
            channel=_WorkaroundChannel(self.http),
            inner=HttpRequest(endpoint=value),
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

    def get(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.get, self.http)

    def delete(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.delete, self.http)


@dataclass(frozen=True)
class FluentHttpRequest:
    method: HttpMethod
    http: Http

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.request(self.method, value))


@dataclass(frozen=True)
class _RequestAlt:
    inner: HttpRequest
    channel: HttpChannel

    def post(self) -> FluentHttpResponse:
        return FluentHttpResponse(
            self.channel.transport(self.inner).over(HttpMethod.post)
        )

    def get(self) -> FluentHttpResponse:
        return FluentHttpResponse(
            self.channel.transport(self.inner).over(HttpMethod.get)
        )

    def patch(self) -> FluentHttpResponse:
        return FluentHttpResponse(
            self.channel.transport(self.inner).over(HttpMethod.patch)
        )

    def delete(self) -> FluentHttpResponse:
        return FluentHttpResponse(
            self.channel.transport(self.inner).over(HttpMethod.delete)
        )

    def put(self) -> FluentHttpResponse:
        return FluentHttpResponse(
            self.channel.transport(self.inner).over(HttpMethod.put)
        )


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
