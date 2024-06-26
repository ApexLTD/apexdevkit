from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from apexdevkit.error import DoesNotExistError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.sample_api import FailingService
from tests.resource.setup import FakeApple, setup


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def resource() -> RestResource:
    return RestCollection(
        name=RestfulName("apple"),
        http=TestClient(setup(FailingService(DoesNotExistError))),
    )


def test_should_not_read_unknown(resource: RestResource) -> None:
    (
        resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_update_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_update_many_unknown(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.update_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.replace_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_many_unknown(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.replace_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_delete_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.delete_one()
        .with_id(apple["id"])
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )
