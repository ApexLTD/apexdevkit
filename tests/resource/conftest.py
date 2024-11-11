import pytest
from starlette.testclient import TestClient

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection
from tests.resource.setup import setup


@pytest.fixture
def resource(service: RestfulServiceBuilder) -> RestCollection:
    return RestCollection(
        name=RestfulName("market-apple"),
        http=Httpx(TestClient(setup(service))),
    )


@pytest.fixture
def read_many_resource(service: RestfulServiceBuilder) -> RestCollection:
    return RestCollection(
        name=RestfulName("apple"),
        http=Httpx(TestClient(setup(service))),
    )
