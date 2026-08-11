from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Self

from pypebbles import JsonDict

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.http import HttpMethod, Httpx
from apexdevkit.http.domain import HttpRequest
from apexdevkit.http.domain.response import HttpResponse
from apexdevkit.http.httpx.client import HttpxChannel


@dataclass(frozen=True)
class RestCollection:
    http: Httpx
    name: RestfulName

    request: HttpRequest = HttpRequest()

    def sub_resource(self, name: str, *, item_id: str) -> RestCollection:
        return RestCollection(
            self.http.with_endpoint(self.name.plural).with_endpoint(item_id),
            RestfulName(name),
        )

    def create_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.post,
                self.http,
                self.request.with_endpoint(self.name.plural),
            ),
        )

    def read_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.get,
                self.http,
                self.request.with_endpoint(self.name.plural),
            ),
        )

    def read_many(self, **params: Any) -> _TestRequest:
        request = self.request.with_endpoint(self.name.plural)
        for p, v in params.items():
            request = request.with_param(p, v)

        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.get,
                self.http,
                request,
            ),
        )

    def read_all(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.get,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def update_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.patch,
                self.http,
                self.request.with_endpoint(self.name.plural),
            ),
        )

    def replace_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.put,
                self.http,
                self.request.with_endpoint(self.name.plural),
            ),
        )

    def delete_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            LazyHttpRequest(
                HttpMethod.delete,
                self.http.with_endpoint(self.name.plural),
            ),
        )


@dataclass(frozen=True)
class _TestRequest:
    resource: RestfulName
    request: LazyHttpRequest

    def with_id(self, value: Any) -> _TestRequest:
        return _TestRequest(
            resource=self.resource,
            request=self.request.with_endpoint(value),
        )

    def and_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def from_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def with_data(self, value: JsonDict) -> _TestRequest:
        return _TestRequest(
            resource=self.resource,
            request=self.request.with_json(value),
        )

    @cached_property
    def response(self) -> HttpResponse:
        return self.request()

    def ensure(self) -> _Response:
        response = self.response
        return _Response(
            resource=self.resource,
            json=JsonDict(self.response.json()),
            http_code=response.status,
        )


@dataclass(frozen=True)
class LazyHttpRequest:
    method: HttpMethod
    http: Httpx
    request: HttpRequest | None = None

    def with_endpoint(self, value: Any) -> LazyHttpRequest:
        return LazyHttpRequest(
            method=self.method,
            http=self.http.with_endpoint(str(value)) if not self.request else self.http,
            request=self.request and self.request.with_endpoint(str(value)),
        )

    def with_json(self, value: JsonDict) -> LazyHttpRequest:
        return LazyHttpRequest(
            method=self.method,
            http=self.http.with_json(value) if not self.request else self.http,
            request=self.request and self.request.with_json(value),
        )

    def __call__(self) -> HttpResponse:
        if not self.request:
            return self.http.request(self.method)

        return HttpxChannel(self.http.client).transport(self.request).over(self.method)


@dataclass
class _Response:
    resource: RestfulName
    json: JsonDict
    http_code: int

    def fail(self) -> Self:
        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

    def with_status(self, value: str) -> Self:
        assert self.json.value_of("status").to(str) == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.http_code == value
        assert self.json.value_of("code").to(int) == value

        return self

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        assert self.json.value_of("error").to(dict) == {"message": value}, self.json

        return self

    def and_item(self, value: Any) -> Self:
        return self.with_item(value)

    def with_item(self, value: Any) -> Self:
        return self.with_data(**{self.resource.singular: value})

    def and_collection(self, value: list[Any]) -> Self:
        return self.with_collection(value)

    def with_collection(self, values: list[Any]) -> Self:
        return self.with_data(**{self.resource.plural: values}, count=len(values))

    def with_data(self, **kwargs: Any) -> Self:
        assert self.json.value_of("data").to(dict) == {**kwargs}, self.json

        return self
