from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Self

from pypebbles import JsonDict
from pypebbles.http import HttpMethod, HttpRequest, HttpResponse, HttpTransport

from apexdevkit.fastapi.name import RestfulName


@dataclass(frozen=True)
class RestTransport:
    transporter: HttpTransport

    method: HttpMethod = HttpMethod.get

    def over(self, method: HttpMethod) -> RestTransport:
        return replace(self, method=method)

    def transport(self, request: HttpRequest) -> HttpResponse:
        return self.transporter.deliver(request, using=self.method)


@dataclass(frozen=True)
class RestCollection:
    name: RestfulName
    transport: RestTransport

    request: HttpRequest = HttpRequest()

    def sub_resource(self, name: RestfulName) -> RestCollection:
        return replace(self, name=name)

    def item(self, with_id: Any) -> RestCollection:
        return RestCollection(
            name=self.name,
            transport=self.transport,
            request=self.request.with_endpoint(str(with_id)),
        )

    def dispatch(self, method: HttpMethod) -> _TestRequest:
        return _TestRequest(self.name, self.request, self.transport.over(method))

    def create(self) -> _TestRequest:
        return self.dispatch(HttpMethod.post)

    def read(self, **params: Any) -> _TestRequest:
        request = self.request
        for p, v in params.items():
            request = request.with_param(p, v)

        return replace(self, request=request).dispatch(HttpMethod.get)

    def update(self) -> _TestRequest:
        return self.dispatch(HttpMethod.patch)

    def replace(self) -> _TestRequest:
        return self.dispatch(HttpMethod.put)

    def delete_one(self) -> _TestRequest:
        return self.dispatch(HttpMethod.delete)


@dataclass(frozen=True)
class _TestRequest:
    resource: RestfulName
    request: HttpRequest
    transporter: RestTransport

    def and_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def from_data(self, value: JsonDict) -> _TestRequest:
        return self.with_data(value)

    def with_data(self, value: JsonDict) -> _TestRequest:
        return replace(self, request=self.request.with_json(value))

    def ensure(self) -> ResponseProbe:
        return ResponseProbe(
            resource=self.resource,
            response=self.transporter.transport(self.request),
        )


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
