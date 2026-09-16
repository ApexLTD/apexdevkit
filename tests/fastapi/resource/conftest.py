import pytest
from fastapi.testclient import TestClient
from pypebbles.http import HttpResponse, HttpTransport
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from tests.fastapi.sample_api import setup


@pytest.fixture
def dependency(service: RestfulServiceBuilder) -> DependableBuilder:
    return service.as_dependable()


@pytest.fixture
def transport(dependency: DependableBuilder) -> HttpTransport[HttpResponse]:
    return Httpx(TestClient(setup(dependency)))
