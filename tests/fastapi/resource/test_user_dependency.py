from __future__ import annotations

from dataclasses import dataclass

import pytest
from pypebbles.http import HttpResponse, HttpTransport

from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestRequest
from tests.fastapi.sample_api import FakeApple, SuccessfulService


@pytest.fixture
def service() -> SuccessfulService:
    return SuccessfulService(always_return=FakeApple().json())


@pytest.fixture
def fake_user() -> FakeUser:
    return FakeUser()


@pytest.fixture
def dependency(service: SuccessfulService, fake_user: FakeUser) -> DependableBuilder:
    return service.as_dependable().with_user(fake_user.user)


@dataclass
class FakeUser:
    times_called: int = 0

    def user(self) -> str:
        self.times_called += 1
        return "user"


def test_should_call_extract_user_for_create_one(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_create_one(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
    )

    assert service.user == "user"


def test_should_call_extract_user_for_read_one(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .read()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_read_one(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .read()
    )

    assert service.user == "user"


def test_should_call_extract_user_for_read_all(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    RestRequest.resource(RestfulName("apple")).using(transport).read()

    assert fake_user.times_called == 1


def test_should_persist_user_for_read_all(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    RestRequest.resource(RestfulName("apple")).using(transport).read()

    assert service.user == "user"


def test_should_call_extract_user_for_update_one(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_update_one(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert service.user == "user"


def test_should_call_extract_user_for_replace_one(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .replace()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_replace_one(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .replace()
    )

    assert service.user == "user"


def test_should_call_extract_user_for_delete_one(
    transport: HttpTransport[HttpResponse],
    fake_user: FakeUser,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .delete()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_delete_one(
    transport: HttpTransport[HttpResponse],
    service: SuccessfulService,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .delete()
    )

    assert service.user == "user"
