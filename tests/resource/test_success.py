from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.sample_api import SuccessfulService
from tests.resource.setup import FakeApple, setup


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def resource(apple: JsonDict) -> RestResource:
    return RestCollection(
        name=RestfulName("apple"),
        http=TestClient(setup(SuccessfulService(always_return=apple))),
    )


def test_should_create(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_item(apple)
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


def test_should_read_one(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.read_one()
        .with_id(apple["id"])
        .ensure()
        .success()
        .with_code(200)
        .with_item(apple)
    )


def test_should_read_all(apple: JsonDict, resource: RestResource) -> None:
    resource.read_all().ensure().success().with_code(200).and_collection([apple])


def test_should_update_one(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .success()
        .with_code(200)
    )


def test_should_update_many(apple: JsonDict, resource: RestResource) -> None:
    resource.update_many().from_data(apple).ensure().success().with_code(200)


def test_should_replace_one(apple: JsonDict, resource: RestResource) -> None:
    resource.replace_one().from_data(apple).ensure().success().with_code(200)


def test_should_replace_many(apple: JsonDict, resource: RestResource) -> None:
    resource.replace_many().from_data(apple).ensure().success().with_code(200)


def test_should_delete_one(apple: JsonDict, resource: RestResource) -> None:
    (resource.delete_one().with_id(apple["id"]).ensure().success().with_code(200))


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
