import pytest

from apexdevkit.error import ExistsError

from ..rest import RestRequest, RestTransport
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def service() -> FailingService:
    return FailingService(ExistsError)


def test_should_not_create_existing(transport: RestTransport) -> None:
    (
        RestRequest()
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .ensure(http_code=409)
        .and_api_fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )
