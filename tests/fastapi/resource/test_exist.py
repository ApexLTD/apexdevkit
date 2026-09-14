import pytest

from apexdevkit.error import ExistsError
from apexdevkit.fastapi.name import RestfulName

from ..rest import RestRequest, RestTransport
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(transport: RestTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .from_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(409)
        .and_message("An item<Market-apple> with the  already exists.")
    )
