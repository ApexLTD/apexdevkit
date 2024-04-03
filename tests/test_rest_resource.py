from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import ANY
from uuid import uuid4

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from pydevtools.fastapi import FastApiBuilder
from pydevtools.http import JsonObject
from pydevtools.repository import InMemoryRepository
from pydevtools.testing import RestfulName, RestResource
from pydevtools.testing.rest import RestCollection
from tests.sample_api import Apple, apple_api


@pytest.fixture
def http() -> TestClient:
    return TestClient(
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_dependency(
            apples=InMemoryRepository[Apple]().with_unique(
                criteria=lambda item: f"name<{item.name}>"
            )
        )
        .with_route(apples=apple_api)
        .build()
    )


@pytest.fixture
def resource(http: TestClient) -> RestResource:
    return RestCollection(http, RestfulName("apple"))


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def apple(self) -> JsonObject[str]:
        return JsonObject(
            {
                "name": self.faker.name(),
                "color": self.faker.color(),
            }
        )


fake = Fake()


def test_should_not_read_unknown(resource: RestResource) -> None:
    unknown_id = uuid4()

    (
        resource.read_one()
        .with_id(unknown_id)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An apple with id<{unknown_id}> does not exist.")
    )


def test_should_not_list_anything_when_none_exist(resource: RestResource) -> None:
    resource.read_all().ensure().success().with_code(200).and_collection([])


def test_should_read_with_params(resource: RestResource) -> None:
    apple_one = fake.apple()
    apple_two = fake.apple().with_a(color=apple_one.value_of("color").to(str))

    apples = (
        resource.create_many().from_data(apple_one).and_data(apple_two).unpack_many()
    )
    color = list(apples)[0].value_of("color").to(str)

    (
        resource.read_all()
        .with_params(color=color)
        .ensure()
        .success()
        .with_code(200)
        .and_collection(list(apples))
    )


def test_should_create(resource: RestResource) -> None:
    apple = fake.apple()

    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_item(apple.with_a(id=ANY))
    )


def test_should_persist(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.read_one()
        .with_id(apple.value_of("id").to(str))
        .ensure()
        .success()
        .with_code(200)
        .and_item(apple)
    )


def test_should_not_duplicate(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.create_one()
        .from_data(apple.drop("id"))
        .ensure()
        .fail()
        .with_code(409)
        .message(f"An apple with the name<{apple.value_of('name')}> already exists.")
        .and_item(apple.select("id"))
    )


def test_should_not_patch(resource: RestResource) -> None:
    id_ = uuid4()

    (
        resource.update_one()
        .with_id(id_)
        .and_data(fake.apple().drop("name"))
        .ensure()
        .fail()
        .with_code(400)
        .and_message(f"Patching <{id_}> is not allowed")
    )


def test_should_create_many(resource: RestResource) -> None:
    many_apples = [fake.apple(), fake.apple()]

    (
        resource.create_many()
        .from_data(many_apples[0])
        .and_data(many_apples[1])
        .ensure()
        .success()
        .with_code(201)
        .and_collection(
            [
                many_apples[0].with_a(id=ANY),
                many_apples[1].with_a(id=ANY),
            ]
        )
    )


def test_should_persist_many(resource: RestResource) -> None:
    apples = (
        resource.create_many()
        .from_data(fake.apple())
        .and_data(fake.apple())
        .unpack_many()
    )

    resource.read_all().ensure().success().with_code(200).and_collection(list(apples))


def test_should_not_duplicate_many(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.create_many()
        .from_data(apple.drop("id"))
        .and_data(apple.drop("id"))
        .ensure()
        .fail()
        .with_code(409)
        .message(f"An apple with the name<{apple.value_of('name')}> already exists.")
        .and_item(apple.select("id"))
    )


def test_should_not_delete_unknown(resource: RestResource) -> None:
    unknown_id = uuid4()

    (
        resource.delete_one()
        .with_id(unknown_id)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An apple with id<{unknown_id}> does not exist.")
    )


def test_should_delete(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.delete_one()
        .with_id(apple.value_of("id").to(str))
        .ensure()
        .success()
        .with_code(200)
        .and_no_data()
    )


def test_should_persist_delete(resource: RestResource) -> None:
    id_ = resource.create_one().from_data(fake.apple()).unpack().value_of("id").to(str)

    resource.delete_one().with_id(id_).ensure().success()

    (
        resource.read_one()
        .with_id(id_)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An apple with id<{id_}> does not exist.")
    )
