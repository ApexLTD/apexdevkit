from __future__ import annotations

from unittest.mock import ANY
from uuid import uuid4

import pytest

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import FakeApple, SuccessfulService


@pytest.fixture
def fake_apple() -> FakeApple:
    return FakeApple()


@pytest.fixture
def service(fake_apple: FakeApple) -> SuccessfulService:
    return SuccessfulService(always_return=fake_apple.entity())


def test_should_create(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .create()
        .ensure(http_code=201)
        .and_api_success()
        .with_code(201)
        .and_item(apple.with_a(id=ANY))
    )

    assert service.called_with == fake_apple.entity(id=ANY)


def test_should_read_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

    (
        RestRequest()
        .item(with_id=apple.value_of("id").to(str))
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_item(apple.with_a(id=ANY))
    )

    assert service.called_with == apple.value_of("id").to(str)


def test_should_read_many(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

    (
        RestRequest()
        .with_params(color="red")
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([apple.with_a(id=ANY)])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_all(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

    (
        RestRequest()
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([apple.with_a(id=ANY)])
    )

    assert service.called_with == {"color": None}


def test_should_update_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

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

    assert service.called_with == fake_apple.entity(id=ANY)


def test_should_replace_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

    (
        RestRequest()
        .with_data(apple)
        .using(transport)
        .replace()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == fake_apple.entity(id=apple.get("id"))


def test_should_delete_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    apple = fake_apple.json()

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
