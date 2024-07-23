from uuid import uuid4

import pytest

from apexdevkit.error import DoesNotExistError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestResource
from tests.resource.sample_api import FailingService
from tests.resource.setup import FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(DoesNotExistError)


def test_should_not_read_unknown(resource: RestResource) -> None:
    (
        resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )


def test_should_not_update_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )


def test_should_not_update_many_unknown(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.update_many()
        .from_collection([apple])
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.replace_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_many_unknown(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.replace_many()
        .from_collection([apple])
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )


def test_should_not_delete_unknown(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.delete_one()
        .with_id(apple["id"])
        .ensure()
        .fail()
        .with_code(404)
        .and_message("An item<Market-apple> with id<unknown> does not exist.")
    )
