from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Iterable, Self

from fastapi.testclient import TestClient

from apexdevkit.http import Http, HttpUrl, JsonDict
from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.httpx import Httpx


@dataclass
class RestResource:
    http: TestClient | Http
    name: RestfulName

    def __post_init__(self) -> None:
        if isinstance(self.http, TestClient):
            self.http = Httpx(self.http)

    @property
    def _http(self) -> Http:
        assert not isinstance(self.http, TestClient)

        return self.http

    def create_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.post, self.http).with_endpoint(self.name.plural),
        )

    def create_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            request=(
                HttpRequest(HttpMethod.post, self.http)
                .with_endpoint(self.name.plural)
                .with_endpoint("batch")
            ),
        )

    def read_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.get, self.http).with_endpoint(self.name.plural),
        )

    def read_all(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.get, self.http).with_endpoint(self.name.plural),
        )

    def update_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.patch, self.http).with_endpoint(self.name.plural),
        )

    def update_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.patch, self.http).with_endpoint(self.name.plural),
        )

    def replace_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.put, self.http).with_endpoint(self.name.plural),
        )

    def replace_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            request=(
                HttpRequest(HttpMethod.put, self.http)
                .with_endpoint(self.name.plural)
                .with_endpoint("batch")
            ),
        )

    def delete_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(HttpMethod.delete, self.http).with_endpoint(self.name.plural),
        )


@dataclass
class RestCollection(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        assert isinstance(self.http, Httpx), "sub resource only works with Httpx"

        client = self.http.client
        client.base_url = client.base_url.join(self.name.plural)

        return RestItem(self.http, RestfulName(name))


@dataclass
class RestItem(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        assert isinstance(self.http, Httpx), "sub resource only works with Httpx"

        client = self.http.client
        client.base_url = client.base_url.join(self.name.singular)

        return RestItem(self.http, RestfulName(name))


@dataclass
class RestfulName:
    singular: str

    plural: str = ""

    def __post_init__(self) -> None:
        self.plural = self.plural or as_plural(self.singular)

    def __add__(self, other: str) -> str:
        return HttpUrl(self.plural) + other


def as_plural(singular: str) -> str:
    if singular.endswith("y"):
        return singular[:-1] + "ies"

    if singular.endswith("ch") or singular.endswith("sh") or singular.endswith("ss"):
        return singular[:-2] + "es"

    if singular.endswith("s") or singular.endswith("z") or singular.endswith("x"):
        return singular[:-1] + "es"

    if singular.endswith("fe"):
        return singular[:-2] + "ves"

    if singular.endswith("f"):
        return singular[:-1] + "ves"

    return singular + "s"


@dataclass
class HttpRequest:
    method: HttpMethod
    http: Http

    endpoint: str = ""

    def with_endpoint(self, value: Any) -> HttpRequest:
        self.endpoint = HttpUrl(self.endpoint) + str(value)

        return self

    def with_param(self, name: str, value: Any) -> HttpRequest:
        self.http = self.http.with_param(name, value)

        return self

    def with_json(self, value: JsonDict) -> HttpRequest:
        self.http = self.http.with_json(value)

        return self

    def __call__(self):
        return self.http.request(method=self.method, endpoint=self.endpoint)


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


@dataclass
class RestResponse:
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
        assert self.json.value_of("error").to(dict) == {"message": value}, self.json

        return self

    def and_item(self, value: Any) -> Self:
        return self.with_item(value)

    def with_item(self, value: Any) -> Self:
        return self.with_data(
            **{
                self.resource.singular: dict(value)
                if isinstance(value, JsonDict)
                else value
            }
        )

    def and_collection(self, value: list[Any]) -> Self:
        return self.with_collection(value)

    def with_collection(self, values: list[Any]) -> Self:
        return self.with_data(
            **{
                self.resource.plural: [
                    dict(value) if isinstance(value, JsonDict) else value
                    for value in values
                ],
            },
            count=len(values),
        )

    def and_no_data(self) -> Self:
        return self.no_data()

    def no_data(self) -> Self:
        return self.with_data()

    def with_data(self, **kwargs: Any) -> Self:
        assert self.json.value_of("data").to(dict) == {**kwargs}, self.json

        return self
