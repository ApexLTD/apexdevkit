import pytest
from fastapi.testclient import TestClient
from pypebbles.http import HttpRequest, HttpTransport
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestCollection, RestTransport
from tests.fastapi.sample_api import setup


@pytest.fixture
def resource(transport: HttpTransport) -> RestCollection:
    return RestCollection(
        name=RestfulName("market-apple"),
        transport=RestTransport(transport),
        request=HttpRequest().with_endpoint("market-apples"),
    )


@pytest.fixture
def read_many_resource(transport: HttpTransport) -> RestCollection:
    return RestCollection(
        name=RestfulName("apple"),
        transport=RestTransport(transport),
        request=HttpRequest().with_endpoint("apples"),
    )


@pytest.fixture
def transport(service: RestfulServiceBuilder) -> HttpTransport:
    return Httpx(TestClient(setup(service)))
