from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Iterable, Self

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.request import HttpRequest
from apexdevkit.fastapi.response import RestResponse
from apexdevkit.http import Http, HttpMethod, JsonDict
from apexdevkit.http.fluent import HttpResponse


@dataclass(frozen=True)
class RestResource:
    http: Http
    name: RestfulName

    def create_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.post,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def create_many(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.post,
                self.http.with_endpoint(self.name.plural).with_endpoint("batch"),
            ),
        )

    def read_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.get,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def read_all(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.get,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def update_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.patch,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def update_many(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.patch,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def replace_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.put,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def replace_many(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.put,
                self.http.with_endpoint(self.name.plural).with_endpoint("batch"),
            ),
        )

    def delete_one(self) -> _TestRequest:
        return _TestRequest(
            self.name,
            HttpRequest(
                HttpMethod.delete,
                self.http.with_endpoint(self.name.plural),
            ),
        )


@dataclass
class _TestRequest:
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


@dataclass(frozen=True)
class RestCollection(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.plural), RestfulName(name))


@dataclass(frozen=True)
class RestItem(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.singular), RestfulName(name))
