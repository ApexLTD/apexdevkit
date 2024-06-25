import pytest
from starlette.testclient import TestClient

from apexdevkit.error import ExistsError
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.setup import setup
from tests.sample_api import FakeServiceBuilder
from tests.resource.test_resource import FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def infra(apple: JsonDict) -> FakeServiceBuilder:
    return FakeServiceBuilder().with_exception(ExistsError()).always_return(apple)


@pytest.fixture
def resource(infra: FakeServiceBuilder) -> RestResource:
    return RestCollection(TestClient(setup(infra)), RestfulName("apple"))


def test_should_not_create_existing(apple: JsonDict, resource: RestResource) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )


def test_should_not_create_many_existing(
    apple: JsonDict, resource: RestResource
) -> None:
    (
        resource.create_many()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message("An item<Apple> with the  already exists.")
    )
