from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypebbles.http import HttpTransport
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import FastApiBuilder, RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestRequest
from tests.fastapi.sample_api import AppleFields, FakeApple, SuccessfulService


@pytest.fixture
def infra() -> RestfulServiceBuilder:
    return SuccessfulService(always_return=FakeApple().json())


@pytest.fixture
def fake_user() -> FakeUser:
    return FakeUser()


@pytest.fixture
def dependency(infra: RestfulServiceBuilder, fake_user: FakeUser) -> DependableBuilder:
    return infra.as_dependable().with_user(fake_user.user)


@pytest.fixture
def transport(dependency: DependableBuilder) -> HttpTransport:
    return Httpx(TestClient(setup(dependency)))


@dataclass
class FakeUser:
    times_called: int = 0

    def user(self) -> str:
        self.times_called += 1
        return "user"


def setup(dependency: DependableBuilder) -> FastAPI:
    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=(
                RestfulRouter.named("apple")
                .with_fields(AppleFields())
                .with_default_dependency(dependency)
                .with_create_one()
                .with_read_one()
                .with_read_all()
                .with_update_one()
                .with_replace_one()
                .with_delete_one()
                .build()
            )
        )
        .build()
    )


def test_should_call_extract_user_for_create_one(
    transport: HttpTransport,
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
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .create()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_read_one(
    transport: HttpTransport,
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
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .read()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_read_all(
    transport: HttpTransport,
    fake_user: FakeUser,
) -> None:
    RestRequest.resource(RestfulName("apple")).using(transport).read()

    assert fake_user.times_called == 1


def test_should_persist_user_for_read_all(
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    RestRequest.resource(RestfulName("apple")).using(transport).read()

    assert infra.user == "user"


def test_should_call_extract_user_for_update_one(
    transport: HttpTransport,
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
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_replace_one(
    transport: HttpTransport,
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
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .with_data(FakeApple().json())
        .using(transport)
        .replace()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_delete_one(
    transport: HttpTransport,
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
    transport: HttpTransport,
    infra: RestfulServiceBuilder,
) -> None:
    (
        RestRequest.resource(RestfulName("apple"))
        .item(with_id=FakeApple().json().get("id"))
        .using(transport)
        .delete()
    )

    assert infra.user == "user"
