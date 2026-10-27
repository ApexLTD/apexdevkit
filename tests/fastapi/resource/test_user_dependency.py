from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from faker import Faker

from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import FakeApple, SuccessfulService

if TYPE_CHECKING:
    from apexdevkit.fastapi import RestfulServiceBuilder
    from apexdevkit.fastapi.dependable import DependableBuilder


@pytest.fixture
def service() -> SuccessfulService:
    return SuccessfulService(always_return=FakeApple().entity())


@pytest.fixture
def builder(service: SuccessfulService) -> RestfulServiceBuilder:
    return service


@pytest.fixture
def username(faker: Faker) -> str:
    return faker.word()


@pytest.fixture
def dependency(service: SuccessfulService, username: str) -> DependableBuilder:
    return service.as_dependable().with_user(lambda: username)


def test_should_persist_user_for_create_one(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).create()

    assert service.user == username


def test_should_persist_user_for_read_one(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).read()

    assert service.user == username


def test_should_persist_user_for_read_all(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    RestRequest().using(transport).read()

    assert service.user == username


def test_should_persist_user_for_update_one(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    (
        RestRequest()
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert service.user == username


def test_should_persist_user_for_replace_one(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).replace()

    assert service.user == username


def test_should_persist_user_for_delete_one(
    transport: RestTransport,
    service: SuccessfulService,
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).delete()

    assert service.user == username
