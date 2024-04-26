from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Type

from pydevtools.http.json import JsonDict


class Http(Protocol):  # pragma: no cover
    def with_header(self, key: str, value: str) -> Http:
        pass

    def with_param(self, key: str, value: str) -> Http:
        pass

    def post(self, endpoint: str, json: JsonDict) -> HttpResponse:
        pass

    def get(self, endpoint: str) -> HttpResponse:
        pass

    def patch(self, endpoint: str, json: JsonDict) -> HttpResponse:
        pass

    def delete(self, endpoint: str) -> HttpResponse:
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

    def post(self) -> FluentHttpPost:
        return FluentHttpPost(self.http)

    def get(self) -> FluentHttpGet:
        return FluentHttpGet(self.http)

    def patch(self) -> FluentHttpPatch:
        return FluentHttpPatch(self.http)

    def delete(self) -> FluentHttpDelete:
        return FluentHttpDelete(self.http)


@dataclass(frozen=True)
class FluentHttpPost:
    http: Http

    json: JsonDict = field(default_factory=JsonDict)

    def and_json(self, value: JsonDict) -> FluentHttpPost:
        return self.with_json(value)

    def with_json(self, value: JsonDict) -> FluentHttpPost:
        return FluentHttpPost(self.http, json=value)

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.post(value, json=self.json))


@dataclass(frozen=True)
class FluentHttpGet:
    http: Http

    params: dict[str, Any] = field(default_factory=dict)

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.get(value))


@dataclass(frozen=True)
class FluentHttpPatch:
    http: Http

    json: JsonDict = field(default_factory=JsonDict)

    def with_json(self, value: JsonDict) -> FluentHttpPatch:
        return FluentHttpPatch(self.http, json=value)

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.patch(value, json=self.json))


@dataclass(frozen=True)
class FluentHttpDelete:
    http: Http

    def on_endpoint(self, value: str) -> FluentHttpResponse:
        return FluentHttpResponse(self.http.delete(value))


@dataclass(frozen=True)
class FluentHttpResponse:
    response: HttpResponse

    def on_bad_request(self, raises: Exception | Type[Exception]) -> FluentHttpResponse:
        if self.response.code() == 400:
            raise raises

        return self

    def on_conflict(self, raises: Exception | Type[Exception]) -> FluentHttpResponse:
        if self.response.code() == 409:
            raise raises

        return self

    def on_failure(self, raises: Type[Exception]) -> FluentHttpResponse:
        if self.response.code() < 200 or self.response.code() > 299:
            raise raises(self.response.raw())

        return self

    def json(self) -> JsonDict:
        return self.response.json()


class HttpResponse(Protocol):
    def code(self) -> int:
        pass

    def raw(self) -> Any:
        pass

    def json(self) -> JsonDict:
        pass
