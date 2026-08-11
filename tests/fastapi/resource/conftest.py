import pytest
from fastapi.testclient import TestClient

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestCollection
from tests.fastapi.sample_api import setup


@pytest.fixture
def resource(service: RestfulServiceBuilder) -> RestCollection:
    return RestCollection(
        name=RestfulName("market-apple"),
        http=TestClient(setup(service)),
    )


@pytest.fixture
def read_many_resource(service: RestfulServiceBuilder) -> RestCollection:
    return RestCollection(
        name=RestfulName("apple"),
        http=TestClient(setup(service)),
    )
