import pytest
from starlette.testclient import TestClient

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.http import Httpx
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.resource.setup import setup


@pytest.fixture
def resource(service: RestfulServiceBuilder) -> RestResource:
    return RestCollection(
        name=RestfulName("market-apple"),
        http=Httpx(TestClient(setup(service))),
    )
