from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from apexdevkit.fastapi import (
    FastApiBuilder,
    RestfulServiceBuilder,
)
from apexdevkit.fastapi.dependable import (
    InfraDependency,
    ServiceDependency,
    UserDependency,
)
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.sample_api import AppleFields


def resource_with_dependency(dependency: ServiceDependency) -> RestResource:
    return RestCollection(
        name=RestfulName("apple"),
        http=Httpx(
            TestClient(
                FastApiBuilder()
                .with_route(
                    apples=RestfulRouter()
                    .with_name(RestfulName("apple"))
                    .with_fields(AppleFields())
                    .default(dependency)
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


def test_should_build_dependable_with_user(
    user: Any, extract_user: Callable[..., Any]
) -> None:
    infra = MagicMock(spec=RestfulServiceBuilder)
    dependency = ServiceDependency(UserDependency(extract_user, InfraDependency(infra)))

    resource_with_dependency(dependency).read_all().ensure()

    infra.with_user.assert_called_once_with(user)
    infra.with_user().build.assert_called_once()
