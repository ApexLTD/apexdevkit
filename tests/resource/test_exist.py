import pytest

from apexdevkit.error import ExistsError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestResource
from tests.resource.sample_api import FailingService
from tests.resource.setup import FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )


def test_should_not_create_many_existing(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.create_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )
