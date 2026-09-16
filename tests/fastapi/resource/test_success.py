from __future__ import annotations

from uuid import uuid4

import pytest
from pypebbles import JsonDict
from pypebbles.http import HttpResponse, HttpTransport

from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestRequest
from tests.fastapi.sample_api import FakeApple, SuccessfulService


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service(apple: JsonDict) -> SuccessfulService:
    return SuccessfulService(always_return=apple)


def test_should_create(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .with_data(apple)
        .using(transport)
        .create()
        .success()
        .with_code(201)
        .and_item(apple)
    )

    assert service.called_with == apple.drop("id")


def test_should_read_one(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .item(with_id=apple.value_of("id").to(str))
        .using(transport)
        .read()
        .success()
        .with_code(200)
        .with_item(apple)
    )

    assert service.called_with == apple.value_of("id").to(str)


def test_should_read_many(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .with_params(color="red")
        .using(transport)
        .read()
        .success()
        .with_code(200)
        .with_collection([apple])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_all(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .using(transport)
        .read()
        .success()
        .with_code(200)
        .and_collection([apple])
    )

    assert service.called_with == {"color": None}


def test_should_update_one(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .item(with_id=apple.value_of("id"))
        .with_data(apple)
        .using(transport)
        .update()
        .success()
        .with_code(200)
    )

    assert service.called_with == (apple["id"], apple.drop("id").drop("color"))


def test_should_replace_one(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .with_data(apple)
        .using(transport)
        .replace()
        .success()
        .with_code(200)
    )

    assert service.called_with == apple


def test_should_delete_one(
    apple: JsonDict,
    service: SuccessfulService,
    transport: HttpTransport[HttpResponse],
) -> None:
    (
        RestRequest(RestfulName("apple"))
        .item(with_id=apple.value_of("id"))
        .using(transport)
        .delete()
        .success()
        .with_code(200)
    )

    assert service.called_with == apple["id"]


def test_should_sub_resource(transport: HttpTransport[HttpResponse]) -> None:
    (
        RestRequest(RestfulName("apple"))
        .item(with_id=str(uuid4()))
        .sub_resource(name=RestfulName("price"))
        .using(transport)
        .delete()
        .success()
        .with_code(200)
    )
