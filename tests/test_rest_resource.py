from __future__ import annotations

import random
from dataclasses import dataclass, field
from unittest.mock import ANY
from uuid import uuid4

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.sample_api import setup, Color


@pytest.fixture
def http() -> TestClient:
    return TestClient(setup())


@pytest.fixture
def resource(http: TestClient) -> RestResource:
    return RestCollection(http, RestfulName("apple"))


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def apple(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(name=self.faker.name())
            .and_a(color=random.choice(list(Color)).value)
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
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
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
        .message(
            f"An item<Apple> with the name<{apple.value_of('name')}> already exists."
        )
        .and_item(apple.select("id"))
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


def test_should_not_update_unknown(resource: RestResource) -> None:
    unknown_id = uuid4()

    (
        resource.update_one()
        .with_id(unknown_id)
        .and_data(fake.apple().drop("id"))
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_update_one(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.update_one()
        .with_id(apple.value_of("id").to(str))
        .and_data(apple.drop("color").with_a(color="RED"))
        .ensure()
        .success()
        .with_code(200)
        .and_no_data()
    )


def test_should_persist_update(resource: RestResource) -> None:
    apple = (
        resource.create_one()
        .from_data(fake.apple())
        .unpack()
        .drop("color")
        .with_a(color="RED")
    )

    (
        resource.update_one()
        .with_id(apple.value_of("id").to(str))
        .and_data(apple)
        .ensure()
        .success()
    )

    (
        resource.read_one()
        .with_id(apple.value_of("id").to(str))
        .ensure()
        .success()
        .with_code(200)
        .and_item(apple)
    )


def test_should_update_many(resource: RestResource) -> None:
    apple_1 = resource.create_one().from_data(fake.apple()).unpack()
    apple_2 = resource.create_one().from_data(fake.apple()).unpack()
    apple_1 = apple_1.drop("color").with_a(color="RED")
    apple_2 = apple_2.drop("color").with_a(color="RED")

    (
        resource.update_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .success()
        .with_code(200)
    )

    resource.read_all().ensure().success().with_code(200).and_collection(
        [apple_1, apple_2]
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
        .message(
            f"An item<Apple> with the name<{apple.value_of('name')}> already exists."
        )
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
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
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
        .and_message(f"An item<Apple> with id<{id_}> does not exist.")
    )
