import pytest
from fastapi.testclient import TestClient
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulApiBuilder
from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.service import RestfulApi, RestfulService
from apexdevkit.testing import RestTransport
from tests.fastapi.sample_api import AppleFormatter, setup


@pytest.fixture
def builder(service: RestfulService) -> PreBuilt:
    return PreBuilt(
        RestfulApi(
            inner=service,
            formatter=AppleFormatter(),
        )
    )


@pytest.fixture
def dependency(builder: RestfulApiBuilder) -> DependableBuilder:
    return builder.as_dependable()


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
