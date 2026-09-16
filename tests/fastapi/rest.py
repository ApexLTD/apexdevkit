from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field, replace
from typing import Any, Self

from pypebbles import JsonDict
from pypebbles.http import (
    HttpDispatcher,
    HttpMethod,
    HttpRequest,
    HttpResponse,
    HttpTransport,
)

from apexdevkit.fastapi.name import RestfulName


@dataclass(frozen=True)
class RestRequest:
    request: HttpRequest = HttpRequest()

    def with_params(self, **params: Any) -> RestRequest:
        return replace(self, request=self.request.with_params(params))

    def with_data(self, value: JsonDict) -> RestRequest:
        return replace(self, request=self.request.with_json(value))

    def sub_resource(self, name: RestfulName) -> RestRequest:
        return replace(self, request=self.request.with_endpoint(name.plural))

    def item(self, with_id: Any) -> RestRequest:
        return replace(self, request=self.request.with_endpoint(str(with_id)))

    def using(self, transport: RestTransport) -> RestDispatcher:
        return RestDispatcher(request=self.request, transport=transport)


@dataclass(frozen=True)
class RestTransport:
    resource: RestfulName
    transport: HttpTransport[HttpResponse]

    def deliver(self, request: HttpRequest, using: HttpMethod) -> StatusProbe:
        return StatusProbe(
            resource=self.resource,
            response=self.transport.deliver(request, using),
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
class StatusProbe:
    resource: RestfulName
    response: HttpResponse

    def ensure(self, http_code: int) -> ResponseProbe:
        assert self.response.status == http_code

        return ResponseProbe(self.response.load(RestResponse(self.resource)))


@dataclass(frozen=True)
class ResponseProbe:
    response: RestResponse

    def and_api_fail(self) -> Self:
        return self.with_status("fail")

    def and_api_success(self) -> Self:
        return self.with_status("success")

    def with_status(self, value: str) -> Self:
        assert self.response.status() == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.response.code() == value

        return self

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        assert self.response.message() == value, self.response.raw

        return self

    def and_item(self, value: Any) -> Self:
        return self.with_item(value)

    def with_item(self, value: Any) -> Self:
        assert self.response.item() == value, self.response.raw

        return self

    def and_collection(self, value: list[Any]) -> Self:
        return self.with_collection(value)

    def with_collection(self, values: list[Any]) -> Self:
        assert self.response.collection() == values, self.response.raw
        assert self.response.count() == len(values)

        return self


@dataclass(frozen=True)
class RestDispatcher(HttpDispatcher[StatusProbe]):
    def create(self) -> StatusProbe:
        return self.dispatch(HttpMethod.post)

    def read(self) -> StatusProbe:
        return self.dispatch(HttpMethod.get)

    def update(self) -> StatusProbe:
        return self.dispatch(HttpMethod.patch)

    def delete(self) -> StatusProbe:
        return self.dispatch(HttpMethod.delete)

    def replace(self) -> StatusProbe:
        return self.dispatch(HttpMethod.put)
