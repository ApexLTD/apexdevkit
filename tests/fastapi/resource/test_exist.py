import pytest
from pypebbles.http import HttpRequest

from apexdevkit.error import ExistsError
from apexdevkit.fastapi.name import RestfulName

from ..rest import RestRequest, RestResponse, RestTransport
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(transport: RestTransport) -> None:
    (
        RestRequest(
            request=HttpRequest().with_endpoint("market-apples"),
            response=RestResponse(RestfulName("market-apple")),
        )
        .from_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(409)
        .and_message("An item<Market-apple> with the  already exists.")
    )
