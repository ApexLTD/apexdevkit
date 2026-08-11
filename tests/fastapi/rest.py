from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cached_property
from typing import Any, Self

from pypebbles import JsonDict

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.http import HttpMethod
from apexdevkit.http.domain import HttpChannel, HttpRequest
from apexdevkit.http.domain.response import HttpResponse


@dataclass(frozen=True)
class RestCollection:
    name: RestfulName
    channel: HttpChannel

    request: HttpRequest = HttpRequest()

    def sub_resource(self, name: str, *, parent_id: str) -> RestCollection:
        return RestCollection(
            name=RestfulName(name),
            channel=self.channel,
            request=(
                self.request.with_endpoint(self.name.plural).with_endpoint(parent_id)
            ),
        )

    def create_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.post,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )

    def read_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.get,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )

    def read_many(self, **params: Any) -> _TestRequest:
        request = self.request.with_endpoint(self.name.plural)
        for p, v in params.items():
            request = request.with_param(p, v)

        return _TestRequest(
            self.name,
            HttpMethod.get,
            request,
            self.channel,
        )

    def read_all(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.get,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )

    def update_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.patch,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )

    def replace_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.put,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )

    def delete_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpMethod.delete,
            self.request.with_endpoint(self.name.plural),
            self.channel,
        )


@dataclass(frozen=True)
class _TestRequest:
    resource: RestfulName
    method: HttpMethod
    request: HttpRequest
    channel: HttpChannel

    def with_id(self, value: Any) -> _TestRequest:
        return replace(self, request=self.request.with_endpoint(str(value)))

    def and_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def from_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def with_data(self, value: JsonDict) -> _TestRequest:
        return replace(self, request=self.request.with_json(value))

    def ensure(self) -> ResponseProbe:
        return ResponseProbe(resource=self.resource, response=self.response)

    @cached_property
    def response(self) -> HttpResponse:
        return self.channel.transport(self.request).over(self.method)


@dataclass(frozen=True)
class ResponseProbe:
    resource: RestfulName
    response: HttpResponse

    def fail(self) -> Self:
        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

    def with_status(self, value: str) -> Self:
        assert self.response.json().value_of("status").to(str) == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.response.status == value
        assert self.response.json().value_of("code").to(int) == value

        return self

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        actual = self.response.json().value_of("error").to(dict)
        assert actual == {"message": value}, self.response.json()

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
        actual = self.response.json().value_of("data").to(dict)
        assert actual == {**kwargs}, self.response.json()

        return self
