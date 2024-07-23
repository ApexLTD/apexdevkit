from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.sample_api import AppleFields, SuccessfulService
from tests.resource.setup import FakeApple


@pytest.fixture
def infra() -> RestfulServiceBuilder:
    return SuccessfulService(always_return=FakeApple().json())


@pytest.fixture
def fake_user() -> FakeUser:
    return FakeUser()


@pytest.fixture
def resource(infra: RestfulServiceBuilder, fake_user: FakeUser) -> RestResource:
    return RestCollection(
        name=RestfulName("apple"),
        http=Httpx(TestClient(setup(infra, fake_user))),
    )


@dataclass
class FakeUser:
    times_called: int = 0

    def user(self) -> str:
        self.times_called += 1
        return "user"


def setup(infra: RestfulServiceBuilder, fake_user: FakeUser) -> FastAPI:
    dependable = DependableBuilder().from_infra(infra).with_user(fake_user.user)
    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_create_one_endpoint(dependable)
            .with_create_many_endpoint(dependable)
            .with_read_one_endpoint(dependable)
            .with_read_all_endpoint(dependable)
            .with_update_one_endpoint(dependable)
            .with_update_many_endpoint(dependable)
            .with_replace_one_endpoint(dependable)
            .with_replace_many_endpoint(dependable)
            .with_delete_one_endpoint(dependable)
            .build()
        )
        .build()
    )


def test_should_call_extract_user_for_create_one(
    resource: RestResource, fake_user: FakeUser
) -> None:
    resource.create_one().from_data(FakeApple().json()).ensure()

    assert fake_user.times_called == 1


def test_should_persist_user_for_create_one(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    resource.create_one().from_data(FakeApple().json()).ensure()

    assert infra.user == "user"


def test_should_call_extract_user_for_create_many(
    resource: RestResource, fake_user: FakeUser
) -> None:
    (
        resource.create_many()
        .from_collection(
            [
                FakeApple().json(),
                FakeApple().json(),
            ]
        )
        .ensure()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_create_many(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    (
        resource.create_many()
        .from_collection(
            [
                FakeApple().json(),
                FakeApple().json(),
            ]
        )
        .ensure()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_read_one(
    resource: RestResource, fake_user: FakeUser
) -> None:
    resource.read_one().with_id(str(FakeApple().json().get("id"))).ensure()

    assert fake_user.times_called == 1


def test_should_persist_user_for_read_one(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    resource.read_one().with_id(str(FakeApple().json().get("id"))).ensure()

    assert infra.user == "user"


def test_should_call_extract_user_for_read_all(
    resource: RestResource, fake_user: FakeUser
) -> None:
    resource.read_all().ensure()

    assert fake_user.times_called == 1


def test_should_persist_user_for_read_all(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    resource.read_all().ensure()

    assert infra.user == "user"


def test_should_call_extract_user_for_update_one(
    resource: RestResource, fake_user: FakeUser
) -> None:
    (
        resource.update_one()
        .with_id(str(FakeApple().json().get("id")))
        .and_data(FakeApple().json().drop("id").drop("color"))
        .ensure()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_update_one(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    (
        resource.update_one()
        .with_id(str(FakeApple().json().get("id")))
        .and_data(FakeApple().json().drop("id").drop("color"))
        .ensure()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_update_many(
    resource: RestResource, fake_user: FakeUser
) -> None:
    (
        resource.update_many()
        .from_collection(
            [
                FakeApple().json().drop("color"),
                FakeApple().json().drop("color"),
            ]
        )
        .ensure()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_update_many(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    (
        resource.update_many()
        .from_collection(
            [
                FakeApple().json().drop("color"),
                FakeApple().json().drop("color"),
            ]
        )
        .ensure()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_replace_one(
    resource: RestResource, fake_user: FakeUser
) -> None:
    resource.replace_one().from_data(FakeApple().json()).ensure()

    assert fake_user.times_called == 1


def test_should_persist_user_for_replace_one(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    resource.replace_one().from_data(FakeApple().json()).ensure()

    assert infra.user == "user"


def test_should_call_extract_user_for_replace_many(
    resource: RestResource, fake_user: FakeUser
) -> None:
    (
        resource.replace_many()
        .from_collection(
            [
                FakeApple().json(),
                FakeApple().json(),
            ]
        )
        .ensure()
    )

    assert fake_user.times_called == 1


def test_should_persist_user_for_replace_many(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    (
        resource.replace_many()
        .from_collection(
            [
                FakeApple().json(),
                FakeApple().json(),
            ]
        )
        .ensure()
    )

    assert infra.user == "user"


def test_should_call_extract_user_for_delete_one(
    resource: RestResource, fake_user: FakeUser
) -> None:
    resource.delete_one().with_id(str(FakeApple().json().get("id"))).ensure()

    assert fake_user.times_called == 1


def test_should_persist_user_for_delete_one(
    resource: RestResource,
    infra: RestfulServiceBuilder,
) -> None:
    resource.delete_one().with_id(str(FakeApple().json().get("id"))).ensure()

    assert infra.user == "user"
