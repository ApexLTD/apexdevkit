from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.error import ForbiddenError
from tests.fastapi.rest import RestRequest, RestTransport
from tests.fastapi.sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ForbiddenError)


def test_should_not_create_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .item(with_id=uuid4())
        .using(transport)
        .read()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_many_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .with_params(color="red")
        .using(transport)
        .read()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_all_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .using(transport)
        .read()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_update_forbidden(transport: RestTransport) -> None:
    apple = FakeApple().json()

    (
        RestRequest()
        .item(with_id=apple.value_of("id"))
        .with_data(apple)
        .using(transport)
        .update()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_replace_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .with_data(FakeApple().json())
        .using(transport)
        .replace()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_delete_forbidden(transport: RestTransport) -> None:
    (
        RestRequest()
        .item(with_id=FakeApple().json().value_of("id").to(str))
        .using(transport)
        .delete()
        .ensure(http_code=403)
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )
