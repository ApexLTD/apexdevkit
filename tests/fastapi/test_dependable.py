from unittest.mock import MagicMock

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

_PARENT = RestfulName("apple")
_CHILD = RestfulName("price")


def _resource(dependency: Dependency) -> RestCollection:
    return RestCollection(
        name=_PARENT,
        http=Httpx(
            TestClient(
                FastApiBuilder()
                .with_route(
                    apples=RestfulRouter()
                    .with_name(_PARENT)
                    .with_fields(AppleFields())
                    .with_dependency(dependency)
                    .with_sub_resource(
                        prices=RestfulRouter()
                        .with_name(_CHILD)
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
        _resource(DependableBuilder.from_builder(builder).with_user(lambda: user))
        .read_all()
        .ensure()
    )

    builder.with_user.assert_called_once_with(user)
    builder.with_user().build.assert_called_once()


def test_should_build_dependable_with_parent(faker: Faker) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)

    (
        _resource(DependableBuilder.from_builder(builder).with_parent(_PARENT))
        .sub_resource(parent_id)
        .sub_resource(_CHILD.singular)
        .read_all()
        .ensure()
        .success()
    )

    builder.with_parent.assert_called_once_with(parent_id)
    builder.with_parent().build.assert_called_once()


def test_should_not_build_dependable_when_no_parent(faker: Faker) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)
    builder.with_parent.side_effect = DoesNotExistError(parent_id)

    (
        _resource(DependableBuilder.from_builder(builder).with_parent(_PARENT))
        .sub_resource(parent_id)
        .sub_resource(_CHILD.singular)
        .read_all()
        .ensure()
        .fail()
        .with_code(404)
        .and_message(
            f"An item<{_PARENT.singular.capitalize()}> "
            f"with id<{parent_id}> does not exist."
        )
    )
