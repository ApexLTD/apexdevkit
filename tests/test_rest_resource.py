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
from tests.sample_api import Color, setup


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
            .with_a(id=self.faker.uuid4())
            .and_a(
                name=JsonDict().with_a(
                    common=self.faker.name(),
                    scientific=self.faker.name(),
                )
            )
            .and_a(color=random.choice(list(Color)).value)
        )

    def price(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(id=self.faker.uuid4())
            .and_a(apple_id=self.faker.uuid4())
            .and_a(currency=self.faker.currency()[0])
            .and_a(value=self.faker.random_int(min=0, max=100))
            .and_a(exponent=self.faker.random_int(min=1, max=10))
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


def test_should_read_all(resource: RestResource) -> None:
    apple_one = fake.apple()
    apple_two = fake.apple()

    apples = (
        resource.create_many().from_data(apple_one).and_data(apple_two).unpack_many()
    )

    resource.read_all().ensure().success().with_code(200).and_collection(list(apples))


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
    apple = resource.create_one().from_data(fake.apple()).unpack()
    updates = fake.apple().drop("id").drop("color")

    (
        resource.update_one()
        .with_id(apple.value_of("id").to(str))
        .and_data(updates)
        .ensure()
        .success()
    )

    (
        resource.read_one()
        .with_id(apple.value_of("id").to(str))
        .ensure()
        .success()
        .with_code(200)
        .and_item(apple.drop("name").merge(updates))
    )


def test_should_update_many(resource: RestResource) -> None:
    apple_1 = resource.create_one().from_data(fake.apple()).unpack()
    apple_2 = resource.create_one().from_data(fake.apple()).unpack()
    (
        resource.update_many()
        .from_data(apple_1.drop("color"))
        .and_data(apple_2.drop("color"))
        .ensure()
        .success()
        .with_code(200)
    )


def test_should_persist_update_many(resource: RestResource) -> None:
    apple_1 = resource.create_one().from_data(fake.apple()).unpack()
    apple_2 = resource.create_one().from_data(fake.apple()).unpack()

    updates_1 = fake.apple().drop("color").drop("id").with_a(id=apple_1["id"])
    updates_2 = fake.apple().drop("color").drop("id").with_a(id=apple_2["id"])
    (
        resource.update_many()
        .from_data(updates_1)
        .and_data(updates_2)
        .ensure()
        .success()
        .with_code(200)
    )

    resource.read_all().ensure().success().with_code(200).and_collection(
        [
            updates_1.with_a(color=apple_1["color"]),
            updates_2.with_a(color=apple_2["color"]),
        ]
    )


def test_should_not_update_many(resource: RestResource) -> None:
    apple_1, apple_2 = fake.apple(), fake.apple()

    (
        resource.update_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{apple_1.get('id')}> does not exist.")
    )


def test_should_not_replace_unknown(resource: RestResource) -> None:
    unknown_apple = fake.apple()
    unknown_id = unknown_apple["id"]

    (
        resource.replace_one()
        .from_data(unknown_apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_replace_one(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.replace_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(200)
        .and_no_data()
    )


def test_should_persist_replace(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()
    replaced_apple = fake.apple().drop("id").with_a(id=apple["id"])

    (
        resource.replace_one()
        .from_data(replaced_apple)
        .ensure()
        .success()
        .with_code(200)
        .and_no_data()
    )

    resource.read_one().with_id(apple["id"]).ensure().success().with_code(
        200
    ).with_item(replaced_apple)


def test_should_replace_many(resource: RestResource) -> None:
    apple_1 = resource.create_one().from_data(fake.apple()).unpack()
    apple_2 = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.replace_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .success()
        .with_code(200)
    )


def test_should_persist_replace_many(resource: RestResource) -> None:
    apple_1 = resource.create_one().from_data(fake.apple()).unpack()
    apple_2 = resource.create_one().from_data(fake.apple()).unpack()

    updated_1 = fake.apple().drop("id").with_a(id=apple_1["id"])
    updated_2 = fake.apple().drop("id").with_a(id=apple_2["id"])

    (
        resource.replace_many()
        .from_data(updated_1)
        .and_data(updated_2)
        .ensure()
        .success()
        .with_code(200)
    )

    (
        resource.read_all()
        .ensure()
        .success()
        .with_code(200)
        .and_collection([updated_1, updated_2])
    )


def test_should_not_replace_many(resource: RestResource) -> None:
    apple_1, apple_2 = fake.apple(), fake.apple()

    (
        resource.replace_many()
        .from_data(apple_1)
        .and_data(apple_2)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{apple_1.get('id')}> does not exist.")
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


def test_should_not_list_sub_items_when_none_exist(resource: RestCollection) -> None:
    id_ = resource.create_one().from_data(fake.apple()).unpack().value_of("id").to(str)

    (
        resource.sub_resource(id_)
        .sub_resource("price")
        .read_all()
        .ensure()
        .success()
        .with_code(200)
        .and_collection([])
    )


def test_should_create_sub_resource(resource: RestCollection) -> None:
    id_ = resource.create_one().from_data(fake.apple()).unpack().value_of("id").to(str)
    price = fake.price()

    (
        resource.sub_resource(id_)
        .sub_resource("price")
        .create_one()
        .from_data(price)
        .ensure()
        .success()
        .with_code(201)
        .and_item(price.with_a(id=ANY).and_a(apple_id=id_))
    )


def test_should_persist_sub_resource(resource: RestCollection) -> None:
    id_ = resource.create_one().from_data(fake.apple()).unpack().value_of("id").to(str)

    price = (
        resource.sub_resource(id_)
        .sub_resource("price")
        .create_one()
        .from_data(fake.price())
        .unpack()
    )

    (
        resource.sub_resource(id_)
        .sub_resource("price")
        .read_all()
        .ensure()
        .success()
        .with_code(200)
        .and_collection([price])
    )


def test_should_should_not_create_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())
    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .create_one()
        .from_data(fake.price())
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_should_not_create_many_without_parent_id(
    resource: RestCollection,
) -> None:
    unknown_id = str(uuid4())
    many_prices = [fake.price(), fake.price()]

    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .create_many()
        .from_data(many_prices[0])
        .and_data(many_prices[1])
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_not_read_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())

    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .read_one()
        .with_id(str(fake.price().get("id")))
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_not_read_many_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())

    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .read_all()
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_not_update_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())
    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .update_one()
        .with_id(str(fake.price().get("id")))
        .and_data(fake.price())
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_not_update_many_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())
    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .update_many()
        .from_data(fake.price())
        .and_data(fake.price())
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )


def test_should_not_delete_without_parent_id(resource: RestCollection) -> None:
    unknown_id = str(uuid4())
    (
        resource.sub_resource(unknown_id)
        .sub_resource("price")
        .delete_one()
        .with_id(str(fake.price().get("id")))
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An item<Apple> with id<{unknown_id}> does not exist.")
    )
