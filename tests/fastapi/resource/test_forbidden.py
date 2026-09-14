from uuid import uuid4

import pytest
from pypebbles import JsonDict
from pypebbles.http import HttpTransport

from apexdevkit.error import ForbiddenError
from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestRequest
from tests.fastapi.sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ForbiddenError)


def test_should_not_create_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .item(with_id=uuid4())
        .using(transport)
        .read()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_many_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .using(transport)
        .read(color="red")
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_all_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .using(transport)
        .read()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_update_forbidden(transport: HttpTransport) -> None:
    apple = FakeApple().json()

    (
        RestRequest.resource(RestfulName("market-apple"))
        .item(with_id=apple.value_of("id"))
        .with_data(apple)
        .using(transport)
        .update()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_replace_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .from_data(FakeApple().json())
        .using(transport)
        .replace()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_delete_forbidden(transport: HttpTransport) -> None:
    (
        RestRequest.resource(RestfulName("market-apple"))
        .item(with_id=FakeApple().json().value_of("id").to(str))
        .using(transport)
        .delete()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )
