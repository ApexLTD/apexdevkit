import pytest
from faker import Faker
from fastapi.testclient import TestClient
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulResource
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.service import RestfulService
from apexdevkit.testing import RestTransport
from tests.fastapi.sample_api import (
    Apple,
    AppleFormatter,
    FakeApple,
    SuccessfulService,
    setup,
)


@pytest.fixture
def transport(dependency: DependableBuilder) -> RestTransport:
    return RestTransport(
        resource=RestfulName("apple"),
        transport=Httpx(
            TestClient(
                app=setup(dependency),
                base_url="http://testserver/apples",
            )
        ),
    )


@pytest.fixture
def dependency(
    username: str,
    builder: RestfulResource.Builder[Apple],
) -> DependableBuilder:
    return DependableBuilder.from_builder(builder).with_user(lambda: username)


@pytest.fixture
def username(faker: Faker) -> str:
    return faker.word()


@pytest.fixture
def builder(service: RestfulService[Apple]) -> RestfulResource.Builder[Apple]:
    return RestfulResource.PreBuilt(instance=service, formatter=AppleFormatter())


@pytest.fixture
def service() -> RestfulService[Apple]:
    return SuccessfulService(always_return=FakeApple().entity())
