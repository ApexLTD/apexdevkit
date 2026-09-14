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
    name = RestfulName("market-apple")

    (
        RestRequest.resource(name)
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(409)
        .and_message(f"An item<{name.singular.capitalize()}> with the  already exists.")
    )
