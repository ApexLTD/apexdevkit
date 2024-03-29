from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Self
from uuid import UUID

import httpx

from pydevtools.http import HttpUrl, Httpx, JsonObject
from pydevtools.http.fluent import JsonList


@dataclass
class RestResource:
    http: Httpx
    name: RestfulName

    def create_one(self) -> CreateOne:
        return CreateOne(self.name, self.http)

    def read_one(self) -> ReadOne:
        return ReadOne(self.name, self.http)

    def read_all(self) -> ReadAll:
        return ReadAll(self.name, self.http)

    def update_one(self) -> UpdateOne:
        return UpdateOne(self.name, self.http)

    def create_many(self) -> CreateMany:
        return CreateMany(self.name, self.http)

    def delete_one(self) -> DeleteOne:
        return DeleteOne(self.name, self.http)


@dataclass
class RestfulName:
    singular: str

    @property
    def plural(self) -> str:
        if self.singular.endswith("y"):
            return self.singular[:-1] + "ies"

        return self.singular + "s"

    def __add__(self, other: str) -> str:
        return HttpUrl(self.plural) + other


@dataclass
class RestRequest:
    resource: RestfulName
    http: Httpx

    @abstractmethod
    @cached_property
    def response(self) -> httpx.Response:  # pragma: no cover
        pass

    def unpack(self) -> JsonObject[Any]:
        return JsonObject(self.response.json()["data"][self.resource.singular])

    def unpack_many(self) -> JsonList[Any]:
        items = self.response.json()["data"][self.resource.plural]

        return JsonList([JsonObject(item) for item in items])

    def ensure(self) -> RestResponse:
        return RestResponse(
            resource=self.resource,
            json=JsonObject(self.response.json()),
            http_code=self.response.status_code,
        )


@dataclass
class CreateOne(RestRequest):
    data: JsonObject[Any] = field(init=False)

    def from_data(self, value: JsonObject[Any]) -> Self:
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
    data: JsonObject[Any] = field(init=False)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.patch(self.resource + str(self.item_id), json=dict(self.data))

    def with_id(self, value: str | UUID) -> Self:
        self.item_id = str(value)

        return self

    def and_data(self, value: JsonObject[Any]) -> Self:
        self.data = value

        return self


@dataclass
class CreateMany(RestRequest):
    data: list[JsonObject[Any]] = field(default_factory=list)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.post(
            self.resource + "batch",
            json={self.resource.plural: [dict(data) for data in self.data]},
        )

    def from_data(self, value: JsonObject[Any]) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: JsonObject[Any]) -> Self:
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
    json: JsonObject[Any]
    http_code: int

    def fail(self) -> Self:
        return self.with_status("fail")

    def success(self) -> Self:
        return self.with_status("success")

    def with_status(self, value: str) -> Self:
        assert self.json.value_of("status").to(str) == value

        return self

    def with_code(self, value: int) -> Self:
        assert self.http_code == value
        assert self.json.value_of("code").to(int) == value

        return self

    def and_message(self, value: str) -> Self:
        return self.with_message(value)

    def with_message(self, value: str) -> Self:
        assert self.json.value_of("error").to(dict) == {"message": value}

        return self

    def and_data(self, *values: JsonObject[Any]) -> Self:
        if len(values) == 1:
            return self.with_data(**{self.resource.singular: dict(values[0])})

        return self.with_data(
            **{
                self.resource.plural: [dict(value) for value in values],
                "count": len(values),
            }
        )

    def and_no_data(self) -> Self:
        return self.no_data()

    def no_data(self) -> Self:
        return self.with_data()

    def with_data(self, **kwargs: Any) -> Self:
        assert self.json.value_of("data").to(dict) == {**kwargs}

        return self
