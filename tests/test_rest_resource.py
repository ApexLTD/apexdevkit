from __future__ import annotations

import random
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Type
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from apexdevkit.testing.fake import FakeResource
from tests.sample_api import Apple, Color, Name, setup


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def resource(apple: JsonDict) -> RestResource:
    return RestCollection(TestClient(setup(apple)), RestfulName("apple"))


@pytest.fixture
def not_exists_error_resource(apple: JsonDict) -> RestResource:
    return RestCollection(
        TestClient(setup(apple, DoesNotExistError())), RestfulName("apple")
    )


@pytest.fixture
def forbidden_error_resource(apple: JsonDict) -> RestResource:
    return RestCollection(
        TestClient(setup(apple, ForbiddenError())), RestfulName("apple")
    )


@pytest.fixture
def exists_error_resource(apple: JsonDict) -> RestResource:
    return RestCollection(TestClient(setup(apple, ExistsError())), RestfulName("apple"))


@dataclass
class FakeApple(FakeResource[Apple]):
    id: str | None = None
    name: Name | None = None
    item_type: Type[Apple] = field(default=Apple)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.id or self.fake.uuid(),
            "name": self._name(),
            "color": random.choice(list(Color)).value,
        }

    def _name(self) -> dict[str, Any]:
        name = self.name or Name(self.fake.text(length=10), self.fake.text(length=10))
        return {"scientific": name.scientific, "common": name.common}


def test_should_create(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_item(apple)
    )


def test_should_not_create_existing(
    apple: JsonDict, exists_error_resource: RestResource
) -> None:
    (
        exists_error_resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )


def test_should_not_create_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_create_many(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.create_many()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_collection([apple])
    )


def test_should_not_create_many_existing(
    apple: JsonDict, exists_error_resource: RestResource
) -> None:
    (
        exists_error_resource.create_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )


def test_should_not_create_many_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.create_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_read_one(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.read_one()
        .with_id(apple["id"])
        .ensure()
        .success()
        .with_code(200)
        .with_item(apple)
    )


def test_should_not_read_unknown(not_exists_error_resource: RestResource) -> None:
    (
        not_exists_error_resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_read_forbidden(forbidden_error_resource: RestResource) -> None:
    (
        forbidden_error_resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_read_all(apple: JsonDict, resource: RestResource) -> None:
    resource.read_all().ensure().success().with_code(200).and_collection([apple])


def test_should_not_read_all_forbidden(forbidden_error_resource: RestResource) -> None:
    forbidden_error_resource.read_all().ensure().fail().with_code(403).and_message(
        "Forbidden"
    )


def test_should_update_one(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .success()
        .with_code(200)
    )


def test_should_not_update_unknown(
    apple: JsonDict, not_exists_error_resource: RestResource
) -> None:
    (
        not_exists_error_resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_update_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_update_many(apple: JsonDict, resource: RestResource) -> None:
    resource.update_many().from_data(apple).ensure().success().with_code(200)


def test_should_not_update_many_unknown(
    apple: JsonDict, not_exists_error_resource: RestResource
) -> None:
    (
        not_exists_error_resource.update_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_update_many_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.update_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_replace_one(apple: JsonDict, resource: RestResource) -> None:
    resource.replace_one().from_data(apple).ensure().success().with_code(200)


def test_should_not_replace_unknown(
    apple: JsonDict, not_exists_error_resource: RestResource
) -> None:
    (
        not_exists_error_resource.replace_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.replace_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_replace_many(apple: JsonDict, resource: RestResource) -> None:
    resource.replace_many().from_data(apple).ensure().success().with_code(200)


def test_should_not_replace_many_unknown(
    apple: JsonDict, not_exists_error_resource: RestResource
) -> None:
    (
        not_exists_error_resource.replace_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_many_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.replace_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_delete_one(apple: JsonDict, resource: RestResource) -> None:
    (resource.delete_one().with_id(apple["id"]).ensure().success().with_code(200))


def test_should_not_delete_unknown(
    apple: JsonDict, not_exists_error_resource: RestResource
) -> None:
    (
        not_exists_error_resource.delete_one()
        .with_id(apple["id"])
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_delete_forbidden(
    apple: JsonDict, forbidden_error_resource: RestResource
) -> None:
    (
        forbidden_error_resource.delete_one()
        .with_id(apple["id"])
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_sub_resource(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.sub_resource(str(uuid4()))
        .sub_resource("price")
        .delete_one()
        .with_id(str(uuid4()))
        .ensure()
        .success()
        .with_code(200)
    )
