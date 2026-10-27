import pytest

from apexdevkit.error import ExistsError
from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.service import RestfulServiceWithFormatter
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import AppleFormatter, FailingService, FakeApple


@pytest.fixture
def builder() -> PreBuilt:
    return PreBuilt(
        RestfulServiceWithFormatter(
            inner=FailingService(ExistsError),
            formatter=AppleFormatter(),
        )
    )


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
