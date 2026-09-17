from __future__ import annotations

from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import FakeApple, SuccessfulService


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service(apple: JsonDict) -> SuccessfulService:
    return SuccessfulService(always_return=apple)


def test_should_create(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .create()
        .ensure(http_code=201)
        .and_api_success()
        .with_code(201)
        .and_item(apple)
    )

    assert service.called_with == apple.drop("id")


def test_should_read_one(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.value_of("id").to(str))
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_item(apple)
    )

    assert service.called_with == apple.value_of("id").to(str)


def test_should_read_many(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .with_params(color="red")
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([apple])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_all(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([apple])
    )

    assert service.called_with == {"color": None}


def test_should_update_one(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.value_of("id"))
        .with_data(apple)
        .using(transport)
        .update()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == (apple["id"], apple.drop("id").drop("color"))


def test_should_replace_one(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .replace()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == apple


def test_should_delete_one(
    transport: RestTransport,
    apple: JsonDict,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.value_of("id"))
        .using(transport)
        .delete()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == apple["id"]


def test_should_sub_resource(transport: RestTransport) -> None:
    (
        RestRequest()
        .item(with_id=str(uuid4()))
        .sub_resource(name=RestfulName("price"))
        .item(with_id=str(uuid4()))
        .using(transport)
        .delete()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )
