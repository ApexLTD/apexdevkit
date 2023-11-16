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
        return JsonList(self.response.json()["data"][self.resource.plural])

    def ensure(self) -> RestResponse:
        return RestResponse(
            http_code=self.response.status_code,
            json=JsonObject(self.response.json()),
        )


@dataclass
class CreateOne(RestRequest):
    data: dict[str, Any] = field(init=False)

    def from_data(self, value: dict[str, Any]) -> Self:
        self.data = value

        return self

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.post(self.resource + "", json=self.data)


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
    @cached_property
    def response(self) -> httpx.Response:
        return self.http.get(self.resource + "")


@dataclass
class UpdateOne(RestRequest):
    item_id: str | UUID = field(init=False)
    data: dict[str, Any] = field(init=False)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.patch(self.resource + str(self.item_id), json=self.data)

    def with_id(self, value: str | UUID) -> Self:
        self.item_id = str(value)

        return self

    def and_data(self, value: dict[str, Any]) -> Self:
        self.data = value

        return self


@dataclass
class CreateMany(RestRequest):
    data: list[dict[str, Any]] = field(default_factory=list)

    @cached_property
    def response(self) -> httpx.Response:
        return self.http.post(
            self.resource + "batch",
            json={self.resource.plural: self.data},
        )

    def from_data(self, value: dict[str, Any]) -> Self:
        self.data.append(value)

        return self

    def and_data(self, value: dict[str, Any]) -> Self:
        return self.from_data(value)


@dataclass
class RestResponse:
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

    def and_data(self, **kwargs: Any) -> Self:
        return self.with_data(**kwargs)

    def and_no_data(self) -> Self:
        return self.no_data()

    def no_data(self) -> Self:
        return self.with_data()

    def with_data(self, **kwargs: Any) -> Self:
        assert self.json.value_of("data").to(dict) == {**kwargs}

        return self
