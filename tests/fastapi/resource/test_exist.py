import pytest

from apexdevkit.error import ExistsError
from apexdevkit.http import JsonDict
from apexdevkit.testing.rest import RestCollection
from tests.fastapi.sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Market-apple> with the  already exists.")
    )


def test_should_not_create_many_existing(
    apple: JsonDict, resource: RestCollection
) -> None:
    (
        resource.create_many()
        .from_collection([apple])
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Market-apple> with the  already exists.")
    )
