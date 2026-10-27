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
    (
        RestRequest()
        .with_data(fake_apple.json())
        .using(transport)
        .create()
        .ensure(http_code=201)
        .and_api_success()
        .with_code(201)
        .and_item(fake_apple.json().with_a(id=ANY))
    )

    assert service.called_with == fake_apple.entity(id=ANY)


def test_should_read_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=fake_apple.entity().id)
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_item(fake_apple.json().with_a(id=ANY))
    )

    assert service.called_with == fake_apple.entity().id


def test_should_read_many(
    transport: RestTransport,
    fake_apple: FakeApple,
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
        .and_collection([fake_apple.json().with_a(id=ANY)])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_all(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([fake_apple.json().with_a(id=ANY)])
    )

    assert service.called_with == {"color": None}


def test_should_update_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=fake_apple.entity().id)
        .with_data(fake_apple.json())
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
    (
        RestRequest()
        .with_data(fake_apple.json())
        .using(transport)
        .replace()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == fake_apple.entity(id=fake_apple.json().get("id"))


def test_should_delete_one(
    transport: RestTransport,
    fake_apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=fake_apple.entity().id)
        .using(transport)
        .delete()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    assert service.called_with == fake_apple.entity().id


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
