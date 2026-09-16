from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Self

from pypebbles import JsonDict
from pypebbles.http import HttpMethod, HttpRequest, HttpResponse, HttpTransport

from apexdevkit.fastapi.name import RestfulName


@dataclass(frozen=True)
class RestRequest:
    request: HttpRequest
    response: RestResponse

    @classmethod
    def resource(cls, name: RestfulName) -> RestRequest:
        return cls(
            request=HttpRequest(),
            response=RestResponse(name),
        )

    def with_params(self, **params: Any) -> RestRequest:
        return replace(self, request=self.request.with_params(params))

    def with_data(self, value: JsonDict) -> RestRequest:
        return replace(self, request=self.request.with_json(value))

    def sub_resource(self, name: RestfulName) -> RestRequest:
        return replace(self, response=RestResponse(name))

    def item(self, with_id: Any) -> RestRequest:
        return replace(self, request=self.request.with_endpoint(str(with_id)))

    def using(self, transport: HttpTransport[HttpResponse]) -> RestDispatcher:
        return self.using_alt(
            transport=RestTransport(
                response=self.response,
                transport=transport,
            ),
        )

    def using_alt(self, transport: RestTransport) -> RestDispatcher:
        return RestDispatcher(
            request=self.request,
            transport=transport,
        )


@dataclass(frozen=True)
class RestTransport:
    response: RestResponse
    transport: HttpTransport[HttpResponse]

    def deliver(self, request: HttpRequest, using: HttpMethod) -> ResponseProbe:
        http_response = self.transport.deliver(request, using)

        return ResponseProbe(
            http_response=http_response,
            rest_response=http_response.load(self.response),
        )


@dataclass(frozen=True)
class RestDispatcher:
    request: HttpRequest
    transport: RestTransport

    def create(self) -> ResponseProbe:
        return self.dispatch(RestMethod.create)

    def read(self) -> ResponseProbe:
        return self.dispatch(RestMethod.read)

    def update(self) -> ResponseProbe:
        return self.dispatch(RestMethod.update)

    def replace(self) -> ResponseProbe:
        return self.dispatch(RestMethod.replace)

    def delete(self) -> ResponseProbe:
        return self.dispatch(RestMethod.delete)

    def dispatch(self, method: RestMethod) -> ResponseProbe:
        return self.transport.deliver(self.request, method.as_http())


class RestMethod(Enum):
    create = auto()
    read = auto()
    update = auto()
    delete = auto()
    replace = auto()

    def as_http(self) -> HttpMethod:
        match self:
            case RestMethod.create:
                return HttpMethod.post
            case RestMethod.read:
                return HttpMethod.get
            case RestMethod.update:
                return HttpMethod.patch
            case RestMethod.replace:
                return HttpMethod.put
            case RestMethod.delete:
                return HttpMethod.delete


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
    http_response: HttpResponse
    rest_response: RestResponse

    def fail(self) -> Self:
        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

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
        assert self.rest_response.collection() == values, self.rest_response.raw
        assert self.rest_response.count() == len(values)

        return self
