from __future__ import annotations

from dataclasses import dataclass

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.request import RestRequest, HttpRequest
from apexdevkit.http import Http, HttpMethod


@dataclass(frozen=True)
class RestResource:
    http: Http
    name: RestfulName

    def create_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.post,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def create_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.post,
                self.http.with_endpoint(self.name.plural).with_endpoint("batch"),
            ),
        )

    def read_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.get,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def read_all(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.get,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def update_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.patch,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def update_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.patch,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def replace_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.put,
                self.http.with_endpoint(self.name.plural),
            ),
        )

    def replace_many(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.put,
                self.http.with_endpoint(self.name.plural).with_endpoint("batch"),
            ),
        )

    def delete_one(self) -> RestRequest:
        return RestRequest(
            self.name,
            HttpRequest(
                HttpMethod.delete,
                self.http.with_endpoint(self.name.plural),
            ),
        )


@dataclass(frozen=True)
class RestCollection(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.plural), RestfulName(name))


@dataclass(frozen=True)
class RestItem(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.singular), RestfulName(name))
