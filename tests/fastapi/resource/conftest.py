import pytest
from fastapi.testclient import TestClient
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.testing import RestTransport
from tests.fastapi.sample_api import setup


@pytest.fixture
def dependency(service: RestfulServiceBuilder) -> DependableBuilder:
    return service.as_dependable()


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
