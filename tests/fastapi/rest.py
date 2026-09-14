from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field, replace
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

    def delete(self) -> _TestRequest:
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
            http_response=self.transporter.transport(self.request),
        )


@dataclass(frozen=True)
class RestResponse:
    resource: RestfulName

    raw: JsonDict = field(default_factory=JsonDict)

    def __call__(self, raw: JsonDict) -> RestResponse:
        return replace(self, raw=raw)

    def status(self) -> str:
        return self.raw.value_of("status").to(str)

    def code(self) -> int:
        return self.raw.value_of("code").to(int)

    def message(self) -> str:
        return self.error().value_of("message").to(str)

    def error(self) -> JsonDict:
        return self.raw.value_of("error").to(JsonDict)

    def item(self) -> JsonDict:
        return self.data().value_of(self.resource.singular).to(JsonDict)

    def collection(self) -> Collection[JsonDict]:
        return self.data().value_of(self.resource.plural).to(list)

    def count(self) -> int:
        return self.data().value_of("count").to(int)

    def data(self) -> JsonDict:
        return self.raw.value_of("data").to(JsonDict)


@dataclass(frozen=True)
class ResponseProbe:
    resource: RestfulName
    http_response: HttpResponse

    def fail(self) -> Self:
        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

    @property
    def rest_response(self) -> RestResponse:
        return self.http_response.load(RestResponse(self.resource))

    def with_status(self, value: str) -> Self:
        assert self.rest_response.status() == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.http_response.status == value
        assert self.rest_response.code() == value

        return self

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        assert self.rest_response.message() == value, self.rest_response.raw

        return self

    def and_item(self, value: Any) -> Self:
        return self.with_item(value)

    def with_item(self, value: Any) -> Self:
        assert self.rest_response.item() == value, self.rest_response.raw

        return self

    def and_collection(self, value: list[Any]) -> Self:
        return self.with_collection(value)

    def with_collection(self, values: list[Any]) -> Self:
        assert self.rest_response.collection() == values, self.http_response.json()
        assert self.rest_response.count() == len(values)

        return self

    def with_data(self, **kwargs: Any) -> Self:
        assert self.rest_response.data() == kwargs, self.http_response.json()

        return self
