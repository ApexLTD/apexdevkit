import random
from dataclasses import dataclass, field

import pytest
from faker import Faker
from fastapi import FastAPI
from starlette.testclient import TestClient

from apexdevkit.error import ForbiddenError
from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.service import (
    RawCollection,
    RawCollectionWithId,
    RawItem,
    RestfulService,
)
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.sample_api import (
    AppleFields,
    Color,
)


@pytest.fixture
def resource(http: TestClient) -> RestResource:
    return RestCollection(http, RestfulName("apple"))


@pytest.fixture
def http() -> TestClient:
    return TestClient(setup())


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def apple(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(id=self.faker.uuid4())
            .and_a(
                name=JsonDict().with_a(
                    common=self.faker.name(),
                    scientific=self.faker.name(),
                )
            )
            .and_a(color=random.choice(list(Color)).value)
        )


class ForbiddenInfra(RestfulServiceBuilder, RestfulService):
    def build(self) -> RestfulService:
        return self

    def create_one(self, item: RawItem) -> RawItem:
        raise ForbiddenError()

    def create_many(self, items: RawCollection) -> RawCollection:
        raise ForbiddenError()

    def read_one(self, item_id: str) -> RawItem:
        raise ForbiddenError()

    def read_all(self) -> RawCollection:
        raise ForbiddenError()

    def update_one(self, item_id: str, **fields: RawItem) -> RawItem:
        raise ForbiddenError()

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        raise ForbiddenError()

    def delete_one(self, item_id: str) -> None:
        raise ForbiddenError()


def setup() -> FastAPI:
    infra = ForbiddenInfra()

    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_infra(infra)
            .with_create_one_endpoint()
            .with_create_many_endpoint()
            .with_read_one_endpoint()
            .with_read_all_endpoint()
            .with_update_one_endpoint()
            .with_update_many_endpoint()
            .with_delete_one_endpoint()
            .build()
        )
        .build()
    )


fake = Fake()


def test_should_raise_forbidden_error_on_create_one(resource: RestResource) -> None:
    apple = fake.apple()

    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_raise_forbidden_error_on_create_many(resource: RestResource) -> None:
    apple_1 = fake.apple()
    apple_2 = fake.apple()

    (
        resource.create_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_raise_forbidden_error_on_read_one(resource: RestResource) -> None:
    apple = fake.apple()
    id_ = apple.value_of("id").to(str)

    (
        resource.read_one()
        .with_id(id_)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_raise_forbidden_error_on_read_all(resource: RestResource) -> None:
    (resource.read_all().ensure().fail().with_code(403).and_message("Forbidden"))


def test_should_raise_forbidden_error_on_update_one(resource: RestResource) -> None:
    apple = fake.apple()
    id_ = apple.value_of("id").to(str)
    (
        resource.update_one()
        .with_id(id_)
        .and_data(apple.drop("color").with_a(color="RED"))
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_raise_forbidden_error_on_update_many(resource: RestResource) -> None:
    apple_1 = fake.apple()
    apple_2 = fake.apple()

    (
        resource.update_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_raise_forbidden_error_on_delete_one(resource: RestResource) -> None:
    apple = fake.apple()
    id_ = apple.value_of("id").to(str)

    (
        resource.delete_one()
        .with_id(id_)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )
