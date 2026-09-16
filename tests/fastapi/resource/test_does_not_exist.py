from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.error import DoesNotExistError

from ..rest import RestRequest, RestTransport
from ..sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(DoesNotExistError)


def test_should_not_read_unknown(transport: RestTransport) -> None:
    (
        RestRequest()
        .item(with_id=uuid4())
        .using(transport)
        .read()
        .fail()
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
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_replace_unknown(transport: RestTransport, apple: JsonDict) -> None:
    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .replace()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )


def test_should_not_delete_unknown(transport: RestTransport, apple: JsonDict) -> None:
    (
        RestRequest()
        .item(with_id=apple["id"])
        .using(transport)
        .delete()
        .fail()
        .with_code(404)
        .and_message("An item<Apple> with id<unknown> does not exist.")
    )
