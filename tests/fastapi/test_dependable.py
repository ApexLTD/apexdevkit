from unittest.mock import MagicMock

from faker import Faker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypebbles.http.drivers import Httpx

from apexdevkit.error import DoesNotExistError
from apexdevkit.fastapi import FastApiBuilder, RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.router import Dependency
from tests.fastapi.rest import RestRequest, RestTransport
from tests.fastapi.sample_api import AppleFields, PriceFields

_PARENT = RestfulName("apple")
_CHILD = RestfulName("price")


def _transport(using: Dependency) -> RestTransport:
    return RestTransport(
        resource=RestfulName("apple"),
        transport=Httpx(
            TestClient(
                _setup(using),
                base_url="http://testserver/apples",
            )
        ),
    )


def _setup(using: Dependency) -> FastAPI:
    return (
        FastApiBuilder()
        .with_route(
            apples=(
                RestfulRouter.named(_PARENT.singular)
                .with_fields(AppleFields())
                .with_default_dependency(using)
                .with_sub_resource(
                    prices=(
                        RestfulRouter.named(_CHILD.singular)
                        .child_of(_PARENT.singular)
                        .with_fields(PriceFields())
                        .with_default_dependency(using)
                        .default()
                        .build()
                    )
                )
                .default()
                .build()
            )
        )
        .build()
    )


def test_should_build_dependable_with_user(faker: Faker) -> None:
    user = faker.name()
    builder = MagicMock(spec=RestfulServiceBuilder)
    dependency = DependableBuilder.from_builder(builder).with_user(lambda: user)

    RestRequest().using(_transport(dependency)).read()

    builder.with_user.assert_called_once_with(user)
    builder.with_user().build.assert_called_once()


def test_should_build_dependable_with_parent(faker: Faker) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)
    dependency = DependableBuilder.from_builder(builder).with_parent(_PARENT)

    (
        RestRequest()
        .item(with_id=parent_id)
        .sub_resource(name=_CHILD)
        .using(_transport(dependency))
        .read()
        .ensure(http_code=200)
        .success()
    )

    builder.with_parent.assert_called_once_with(parent_id)
    builder.with_parent().build.assert_called_once()


def test_should_not_build_dependable_when_no_parent(faker: Faker) -> None:
    parent_id = str(faker.uuid4())
    builder = MagicMock(spec=RestfulServiceBuilder)
    builder.with_parent.side_effect = DoesNotExistError(parent_id)

    dependency = DependableBuilder.from_builder(builder).with_parent(_PARENT)
    (
        RestRequest()
        .item(with_id=parent_id)
        .sub_resource(name=_CHILD)
        .using(_transport(dependency))
        .read()
        .ensure(http_code=404)
        .and_api_fail()
        .with_code(404)
        .and_message(
            f"An item<{_PARENT.singular.capitalize()}> "
            f"with id<{parent_id}> does not exist."
        )
    )
