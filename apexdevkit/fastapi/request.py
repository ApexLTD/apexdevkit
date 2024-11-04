from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Iterable, Self

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.response import RestResponse
from apexdevkit.http import Http, HttpMethod, JsonDict
from apexdevkit.http.fluent import HttpResponse


@dataclass
class HttpRequest:
    method: HttpMethod
    http: Http

    def with_endpoint(self, value: Any) -> HttpRequest:
        self.http = self.http.with_endpoint(str(value))

        return self

    def with_param(self, name: str, value: Any) -> HttpRequest:
        self.http = self.http.with_param(name, value)

        return self

    def with_json(self, value: JsonDict) -> HttpRequest:
        self.http = self.http.with_json(value)

        return self

    def __call__(self) -> HttpResponse:
        return self.http.request(self.method)


@dataclass
class RestRequest:
    resource: RestfulName
    request: HttpRequest

    def with_id(self, value: Any) -> Self:
        self.request = self.request.with_endpoint(value)

        return self

    def from_collection(self, value: list[JsonDict]) -> Self:
        return self.with_data(
            JsonDict({self.resource.plural: [dict(item) for item in value]})
        )

    def and_data(self, value: JsonDict) -> Self:
        return self.with_data(value)

    def from_data(self, value: JsonDict) -> Self:
        return self.with_data(value)

    def with_data(self, value: JsonDict) -> Self:
        self.request = self.request.with_json(value)

        return self

    def and_param(self, name: str, value: Any) -> Self:
        return self.with_param(name, value)

    def with_param(self, name: str, value: Any) -> Self:
        self.request = self.request.with_param(name, str(value))

        return self

    @cached_property
    def response(self) -> HttpResponse:
        return self.request()

    def unpack(self) -> JsonDict:
        return JsonDict(self.response.json()["data"][self.resource.singular])

    def unpack_many(self) -> Iterable[JsonDict]:
        items = self.response.json()["data"][self.resource.plural]

        return [JsonDict(item) for item in items]

    def ensure(self) -> RestResponse:
        return RestResponse(
            resource=self.resource,
            json=JsonDict(self.response.json()),
            http_code=self.response.code(),
        )
