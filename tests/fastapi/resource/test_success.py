from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

import pytest

from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.service import RestfulServiceWithFormatter
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import AppleFormatter, FakeApple, SuccessfulService

if TYPE_CHECKING:
    from apexdevkit.fastapi import RestfulServiceBuilder


@pytest.fixture
def apple() -> FakeApple:
    return FakeApple()


@pytest.fixture
def service(apple: FakeApple) -> SuccessfulService:
    return SuccessfulService(always_return=apple.entity())


@pytest.fixture
def builder(service: SuccessfulService) -> RestfulServiceBuilder:
    return PreBuilt(
        RestfulServiceWithFormatter(
            inner=service,
            formatter=AppleFormatter(),
        )
    )


def test_should_create(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .with_data(apple.json())
        .using(transport)
        .create()
        .ensure(http_code=201)
        .and_api_success()
        .with_code(201)
        .and_item(apple.json().with_a(id=ANY))
    )

    service.log.assert_called_with(create_one=apple.entity(id=ANY))


def test_should_read_one(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.entity().id)
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_item(apple.json().with_a(id=ANY))
    )

    service.log.assert_called_with(read_one=apple.entity().id)


def test_should_read_many(
    transport: RestTransport,
    apple: FakeApple,
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
        .and_collection([apple.json().with_a(id=ANY)])
    )

    service.log.assert_called_with(read_many={"color": "red"})


def test_should_read_all(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .using(transport)
        .read()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
        .and_collection([apple.json().with_a(id=ANY)])
    )

    service.log.assert_called_with(read_many={"color": None})


def test_should_update_one(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.entity().id)
        .with_data(apple.json())
        .using(transport)
        .update()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    service.log.assert_called_with(update_one=apple.entity(id=ANY))


def test_should_replace_one(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .with_data(apple.json())
        .using(transport)
        .replace()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    service.log.assert_called_with(update_one=apple.entity(id=apple.json().get("id")))


def test_should_delete_one(
    transport: RestTransport,
    apple: FakeApple,
    service: SuccessfulService,
) -> None:
    (
        RestRequest()
        .item(with_id=apple.entity().id)
        .using(transport)
        .delete()
        .ensure(http_code=200)
        .and_api_success()
        .with_code(200)
    )

    service.log.assert_called_with(delete_one=apple.entity().id)


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
