from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from apexdevkit.error import DoesNotExistError
from apexdevkit.fastapi import FastApiBuilder, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.router import Dependency, RestfulRouter
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection
from tests.fastapi.sample_api import AppleFields, PriceFields


def resource(dependency: Dependency) -> RestCollection:
    return RestCollection(
        name=RestfulName("apple"),
        http=Httpx(
            TestClient(
                FastApiBuilder()
                .with_route(
                    apples=RestfulRouter()
                    .with_name(RestfulName("apple"))
                    .with_fields(AppleFields())
                    .with_dependency(dependency)
                    .with_sub_resource(
                        prices=RestfulRouter()
                        .with_name(RestfulName("price"))
                        .with_fields(PriceFields())
                        .with_dependency(dependency)
                        .default()
                        .build()
                    )
                    .default()
                    .build()
                )
                .build()
            )
        ),
    )


@pytest.fixture
def user() -> Any:
    return "A"


@pytest.fixture
def extract_user(user: Any) -> Callable[..., Any]:
    def _() -> Any:
        return user

    return _


@pytest.fixture
def identifier() -> str:
    return "id"


@pytest.fixture
def parent() -> RestfulName:
    return RestfulName("apple")


@pytest.fixture
def child() -> RestfulName:
    return RestfulName("price")


def test_should_build_dependable_with_user(
    user: Any,
    extract_user: Callable[..., Any],
) -> None:
    infra = MagicMock(spec=RestfulServiceBuilder)

    (
        resource(DependableBuilder.from_callable(lambda: infra).with_user(extract_user))
        .read_all()
        .ensure()
    )

    infra.with_user.assert_called_once_with(user)
    infra.with_user().build.assert_called_once()


def test_should_build_dependable_with_parent(
    identifier: str,
    parent: RestfulName,
    child: RestfulName,
) -> None:
    infra = MagicMock(spec=RestfulServiceBuilder)
    (
        resource(DependableBuilder.from_callable(lambda: infra).with_parent(parent))
        .sub_resource(identifier)
        .sub_resource(child.singular)
        .read_all()
        .ensure()
    )

    infra.with_parent.assert_called_once_with(identifier)
    infra.with_parent().build.assert_called_once()


def test_should_not_build_dependable_when_no_parent(
    identifier: str,
    parent: RestfulName,
    child: RestfulName,
) -> None:
    infra = MagicMock(spec=RestfulServiceBuilder)
    infra.with_parent.side_effect = DoesNotExistError(identifier)

    (
        resource(DependableBuilder.from_callable(lambda: infra).with_parent(parent))
        .sub_resource(identifier)
        .sub_resource(child.singular)
        .read_all()
        .ensure()
        .fail()
        .with_code(404)
        .and_message(
            f"An item<{parent.singular.capitalize()}> "
            f"with id<{identifier}> does not exist."
        )
    )
