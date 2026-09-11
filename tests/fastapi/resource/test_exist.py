import pytest
from pypebbles import JsonDict

from apexdevkit.error import ExistsError

from ..rest import RestCollection
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.create()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Market-apple> with the  already exists.")
    )
