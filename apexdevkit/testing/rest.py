from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Iterable, Self
from uuid import UUID
from warnings import warn

import httpx
from fastapi.testclient import TestClient

from apexdevkit.http import HttpUrl, JsonDict


@dataclass
class RestResource:
    http: TestClient
    name: RestfulName

    def create_one(self) -> CreateOne:
        return CreateOne(self.name, self.http)

    def read_one(self) -> ReadOne:
        return ReadOne(self.name, self.http)

    def read_all(self) -> ReadAll:
        return ReadAll(self.name, self.http)

    def update_one(self) -> UpdateOne:
        return UpdateOne(self.name, self.http)

    def update_many(self) -> UpdateMany:
        return UpdateMany(self.name, self.http)

    def create_many(self) -> CreateMany:
        return CreateMany(self.name, self.http)

    def delete_one(self) -> DeleteOne:
        return DeleteOne(self.name, self.http)


@dataclass
class RestCollection(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(
            TestClient(
                self.http.app,
                base_url=HttpUrl(str(self.http.base_url)) + self.name.plural,
            ),
            RestfulName(name),
        )


@dataclass
class RestItem(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(
            TestClient(
                self.http.app,
                base_url=HttpUrl(str(self.http.base_url)) + self.name.singular,
            ),
            RestfulName(name),
        )


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

    return singular + "s"


@dataclass
class RestRequest:
    resource: RestfulName
    http: TestClient

    @abstractmethod
    @cached_property
    def response(self) -> httpx.Response:  # pragma: no cover
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
            http_code=self.response.status_code,
        )


@dataclass
class CreateOne(RestRequest):
    data: JsonDict = field(init=False)

    def from_data(self, value: JsonDict) -> Self:
        self.data = value

        return self

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.post(self.resource + "", json=dict(self.data))


@dataclass
class ReadOne(RestRequest):
    item_id: str | UUID = field(init=False)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.get(self.resource + str(self.item_id))

    def with_id(self, value: str | UUID) -> Self:
        self.item_id = str(value)

        return self


@dataclass
class ReadAll(RestRequest):
    params: dict[str, Any] = field(init=False, default_factory=dict)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.get(self.resource + "", params=self.params)

    def with_params(self, **kwargs: Any) -> Self:
        self.params = {**kwargs}

        return self


@dataclass
class UpdateOne(RestRequest):
    item_id: str | UUID = field(init=False)
    data: JsonDict = field(init=False)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.patch(self.resource + str(self.item_id), json=dict(self.data))

    def with_id(self, value: str | UUID) -> Self:
        self.item_id = str(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        self.data = value

        return self


@dataclass
class CreateMany(RestRequest):
    data: list[JsonDict] = field(default_factory=list)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.post(
            self.resource + "batch",
            json={self.resource.plural: [dict(data) for data in self.data]},
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
    def response(self) -> httpx.Response:
        return self.http.patch(
            self.resource + "",
            json={self.resource.plural: [dict(data) for data in self.data]},
        )

    def from_data(self, value: JsonDict) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: JsonDict) -> Self:
        return self.from_data(value)


@dataclass
class DeleteOne(RestRequest):
    item_id: str | UUID = field(init=False)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.delete(self.resource + str(self.item_id))

    def with_id(self, value: str | UUID) -> Self:
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

    def and_data(self, *values: JsonDict) -> Self:  # pragma: no cover
        warn(
            (
                "The 'and_data' method is deprecated. "
                "Please use 'and_item' or 'and_collection' instead."
            )
        )
        if len(values) == 1:
            return self.with_item(values[0])

        return self.with_collection(list(values))

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
