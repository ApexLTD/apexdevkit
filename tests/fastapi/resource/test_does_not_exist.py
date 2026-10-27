from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.error import DoesNotExistError
from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.service import RestfulServiceShell
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import AppleFormatter, FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def builder() -> PreBuilt:
    return PreBuilt(
        RestfulServiceShell(
            inner=FailingService(DoesNotExistError),
            formatter=AppleFormatter(),
        )
    )


def test_should_not_read_unknown(transport: RestTransport) -> None:
    (
        RestRequest()
        .item(with_id=uuid4())
        .using(transport)
        .read()
        .ensure(http_code=404)
        .and_api_fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_update_unknown(transport: RestTransport, apple: JsonDict) -> None:
    (
        RestRequest()
        .item(with_id=apple["id"])
        .with_data(apple)
        .using(transport)
        .update()
        .ensure(http_code=404)
        .and_api_fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_unknown(transport: RestTransport, apple: JsonDict) -> None:
    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .replace()
        .ensure(http_code=404)
        .and_api_fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_delete_unknown(transport: RestTransport, apple: JsonDict) -> None:
    (
        RestRequest()
        .item(with_id=apple["id"])
        .using(transport)
        .delete()
        .ensure(http_code=404)
        .and_api_fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )
