from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Protocol

from pypebbles import JsonDict


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


class HttpTransport(Protocol):
    def over(self, method: HttpMethod) -> HttpTransport:
        pass

    def transport(
        self,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        json: JsonDict | None,
        data: JsonDict | None,
    ) -> HttpResponse:
        pass


class HttpMethod(Enum):
    post = auto()
    get = auto()
    patch = auto()
    delete = auto()
    put = auto()


class HttpResponse(Protocol):  # pragma: no cover
    def code(self) -> int:
        pass

    def raw(self) -> Any:
        pass

    def json(self) -> JsonDict:
        pass


@dataclass(frozen=True)
class FluentHttp:
    http: Http

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

    def post(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.post, self.http)

    def get(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.get, self.http)

    def patch(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.patch, self.http)

    def delete(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.delete, self.http)

    def put(self) -> FluentHttpRequest:
        return FluentHttpRequest(HttpMethod.put, self.http)


@dataclass(frozen=True)
class FluentHttpRequest:
    method: HttpMethod
    http: Http

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.request(self.method, value))


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
