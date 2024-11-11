from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Iterable, Self

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.request import HttpRequest
from apexdevkit.http import Http, HttpMethod, JsonDict
from apexdevkit.http.fluent import HttpResponse


@dataclass(frozen=True)
class _RestResource:
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

    def read_many(self, **params: Any) -> _TestRequest:
        http = self.http.with_endpoint(self.name.plural)
        for p, v in params.items():
            http = http.with_param(p, v)

        return _TestRequest(self.name, HttpRequest(HttpMethod.get, http))

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

    def ensure(self) -> _Response:
        return _Response(
            resource=self.resource,
            json=JsonDict(self.response.json()),
            http_code=self.response.code(),
        )


@dataclass
class _Response:
    resource: RestfulName
    json: JsonDict
    http_code: int

    def fail(self) -> Self:
        if self.http_code == 422:
            return self

        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

    def with_status(self, value: str) -> Self:
        assert self.json.value_of("status").to(str) == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.http_code == value

        if self.http_code != 422:
            assert self.json.value_of("code").to(int) == value

        return self

    def message(self, value: str) -> Self:
        return self.with_message(value)

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        assert self.json.value_of("error").as_dict() == {"message": value}, self.json

        return self

    def and_item(self, value: Any) -> Self:
        return self.with_item(value)

    def with_item(self, value: Any) -> Self:
        return self.with_data(**{self.resource.singular: value})

    def and_collection(self, value: list[Any]) -> Self:
        return self.with_collection(value)

    def with_collection(self, values: list[Any]) -> Self:
        return self.with_data(**{self.resource.plural: values}, count=len(values))

    def and_no_data(self) -> Self:
        return self.no_data()

    def no_data(self) -> Self:
        return self.with_data()

    def with_data(self, **kwargs: Any) -> Self:
        assert self.json.value_of("data").as_dict() == {**kwargs}, self.json

        return self


@dataclass(frozen=True)
class RestCollection(_RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.plural), RestfulName(name))


@dataclass(frozen=True)
class RestItem(_RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.singular), RestfulName(name))
