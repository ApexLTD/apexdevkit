import pytest
from pypebbles.http import HttpTransport

from apexdevkit.error import ExistsError
from apexdevkit.fastapi.name import RestfulName

from ..rest import RestRequest
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )
