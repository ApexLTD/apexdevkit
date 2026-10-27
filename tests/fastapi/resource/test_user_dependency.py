from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.service import RestfulServiceWithFormatter
from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import AppleFormatter, FakeApple, SuccessfulService

if TYPE_CHECKING:
    from faker import Faker

    from apexdevkit.fastapi import RestfulServiceBuilder
    from apexdevkit.fastapi.dependable import DependableBuilder


@pytest.fixture
def builder() -> RestfulServiceBuilder:
    return PreBuilt(
        RestfulServiceWithFormatter(
            inner=SuccessfulService(always_return=FakeApple().entity()),
            formatter=AppleFormatter(),
        )
    )


@pytest.fixture
def username(faker: Faker) -> str:
    return faker.word()


@pytest.fixture
def dependency(builder: RestfulServiceBuilder, username: str) -> DependableBuilder:
    return builder.as_dependable().with_user(lambda: username)


def test_should_persist_user_for_create_one(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).create()

    assert builder.user == username


def test_should_persist_user_for_read_one(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).read()

    assert builder.user == username


def test_should_persist_user_for_read_all(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    RestRequest().using(transport).read()

    assert builder.user == username


def test_should_persist_user_for_update_one(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    (
        RestRequest()
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert builder.user == username


def test_should_persist_user_for_replace_one(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).replace()

    assert builder.user == username


def test_should_persist_user_for_delete_one(
    transport: RestTransport,
    builder: RestfulServiceBuilder,
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).delete()

    assert builder.user == username
