from unittest.mock import MagicMock

import pytest
from faker import Faker
from starlette.testclient import TestClient

from apexdevkit.error import DoesNotExistError
from apexdevkit.fastapi import FastApiBuilder, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.router import Dependency, RestfulRouter
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection
from tests.fastapi.sample_api import AppleFields, PriceFields


@pytest.fixture
def parent() -> RestfulName:
    return RestfulName("apple")


@pytest.fixture
def child() -> RestfulName:
    return RestfulName("price")


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


def test_should_build_dependable_with_user(faker: Faker) -> None:
    user = faker.name()
    builder = MagicMock(spec=RestfulServiceBuilder)

    (
        resource(DependableBuilder.from_callable(builder).with_user(lambda: user))
        .read_all()
        .ensure()
    )

    builder().with_user.assert_called_once_with(user)
    builder().with_user().build.assert_called_once()


def test_should_build_dependable_with_parent(
    parent: RestfulName,
    child: RestfulName,
    faker: Faker,
) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)

    (
        resource(DependableBuilder.from_callable(builder).with_parent(parent))
        .sub_resource(parent_id)
        .sub_resource(child.singular)
        .read_all()
        .ensure()
        .success()
    )

    builder().with_parent.assert_called_once_with(parent_id)
    builder().with_parent().build.assert_called_once()


def test_should_not_build_dependable_when_no_parent(
    parent: RestfulName,
    child: RestfulName,
    faker: Faker,
) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)
    builder().with_parent.side_effect = DoesNotExistError(parent_id)

    (
        resource(DependableBuilder.from_callable(builder).with_parent(parent))
        .sub_resource(parent_id)
        .sub_resource(child.singular)
        .read_all()
        .ensure()
        .fail()
        .with_code(404)
        .and_message(
            f"An item<{parent.singular.capitalize()}> "
            f"with id<{parent_id}> does not exist."
        )
    )
