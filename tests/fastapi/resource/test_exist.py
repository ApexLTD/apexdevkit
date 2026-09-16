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
        RestRequest(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )
