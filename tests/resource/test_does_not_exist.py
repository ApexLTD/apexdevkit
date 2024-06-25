from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from apexdevkit.error import DoesNotExistError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.setup import setup
from tests.sample_api import FakeServiceBuilder
from tests.test_rest_resource import FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def infra(apple: JsonDict) -> FakeServiceBuilder:
    return FakeServiceBuilder().with_exception(DoesNotExistError()).always_return(apple)


@pytest.fixture
def not_exists_error_resource(infra: FakeServiceBuilder) -> RestResource:
    return RestCollection(TestClient(setup(infra)), RestfulName("apple"))


def test_should_not_read_unknown(not_exists_error_resource: RestResource) -> None:
    (
        not_exists_error_resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
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
