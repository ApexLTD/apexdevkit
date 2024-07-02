from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Iterable, Self

from fastapi.testclient import TestClient

from apexdevkit.http import Http, HttpUrl, HttpxConfig, JsonDict
from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.httpx import Httpx


@dataclass
class RestResource:
    http: TestClient | Http
    name: RestfulName

    def __post_init__(self) -> None:
        if isinstance(self.http, TestClient):
            self.http = Httpx(self.http, HttpxConfig())

    @property
    def _http(self) -> Http:
        assert not isinstance(self.http, TestClient)

        return self.http

    def create_one(self) -> CreateOne:
        return CreateOne(self.name, self._http)

    def create_many(self) -> CreateMany:
        return CreateMany(self.name, self._http)

    def read_one(self) -> ReadOne:
        return ReadOne(self.name, self._http)

    def read_all(self) -> ReadAll:
        return ReadAll(self.name, self._http)

    def update_one(self) -> UpdateOne:
        return UpdateOne(self.name, self._http)

    def update_many(self) -> UpdateMany:
        return UpdateMany(self.name, self._http)

    def replace_one(self) -> ReplaceOne:
        return ReplaceOne(self.name, self._http)

    def replace_many(self) -> ReplaceMany:
        return ReplaceMany(self.name, self._http)

    def delete_one(self) -> DeleteOne:
        return DeleteOne(self.name, self._http)


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
        client.base_url = client.base_url.join(self.name.plural)

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
class RestRequest:
    resource: RestfulName
    http: Http

    @abstractmethod
    @cached_property
    def response(self) -> HttpResponse:  # pragma: no cover
        pass

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
class CreateOne(RestRequest):
    data: JsonDict = field(init=False)

    def from_data(self, value: JsonDict) -> Self:
        self.data = value

        return self

    @cached_property
    def response(self) -> HttpResponse:
        return self.http.with_json(self.data).request(
            method=HttpMethod.post,
            endpoint=self.resource + "",
        )


@dataclass
class ReadOne(RestRequest):
    item_id: str = field(init=False)

    @cached_property
    def response(self) -> HttpResponse:
        return self.http.request(
            method=HttpMethod.get,
            endpoint=self.resource + str(self.item_id),
        )

    def with_id(self, value: Any) -> Self:
        self.item_id = str(value)

        return self


@dataclass
class ReadAll(RestRequest):
    params: dict[str, Any] = field(init=False, default_factory=dict)

    @cached_property
    def response(self) -> HttpResponse:
        http = self.http
        for param, value in self.params.items():
            http = http.with_param(param, value)

        return http.request(method=HttpMethod.get, endpoint=self.resource + "")

    def with_params(self, **kwargs: Any) -> Self:
        self.params = {**kwargs}

        return self


@dataclass
class UpdateOne(RestRequest):
    item_id: str = field(init=False)
    data: JsonDict = field(init=False)

    @cached_property
    def response(self) -> HttpResponse:
        return self.http.with_json(self.data).request(
            method=HttpMethod.patch,
            endpoint=self.resource + str(self.item_id),
        )

    def with_id(self, value: Any) -> Self:
        self.item_id = str(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        self.data = value

        return self


@dataclass
class ReplaceOne(RestRequest):
    data: JsonDict = field(init=False)

    @cached_property
    def response(self) -> HttpResponse:
        return self.http.with_json(self.data).request(
            method=HttpMethod.put,
            endpoint=self.resource + "",
        )

    def from_data(self, value: JsonDict) -> Self:
        self.data = value

        return self


@dataclass
class CreateMany(RestRequest):
    data: list[JsonDict] = field(default_factory=list)

    @cached_property
    def response(self) -> HttpResponse:
        json = JsonDict({self.resource.plural: [dict(data) for data in self.data]})

        return self.http.with_json(json).request(
            method=HttpMethod.post,
            endpoint=self.resource + "batch",
        )

    def from_data(self, value: JsonDict) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        return self.from_data(value)


@dataclass
class UpdateMany(RestRequest):
    data: list[JsonDict] = field(default_factory=list)

    @cached_property
    def response(self) -> HttpResponse:
        json = JsonDict({self.resource.plural: [dict(data) for data in self.data]})

        return self.http.with_json(json).request(
            method=HttpMethod.patch,
            endpoint=self.resource + "",
        )

    def from_data(self, value: JsonDict) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        return self.from_data(value)


@dataclass
class ReplaceMany(RestRequest):
    data: list[JsonDict] = field(default_factory=list)

    @cached_property
    def response(self) -> HttpResponse:
        json = JsonDict({self.resource.plural: [dict(data) for data in self.data]})

        return self.http.with_json(json).request(
            method=HttpMethod.put,
            endpoint=self.resource + "batch",
        )

    def from_data(self, value: JsonDict) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        return self.from_data(value)


@dataclass
class DeleteOne(RestRequest):
    item_id: str = field(init=False)

    @cached_property
    def response(self) -> HttpResponse:
        return self.http.request(
            method=HttpMethod.delete,
            endpoint=self.resource + str(self.item_id),
        )

    def with_id(self, value: Any) -> Self:
        self.item_id = str(value)

        return self


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
