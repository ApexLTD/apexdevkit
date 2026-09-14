import pytest
from fastapi.testclient import TestClient
from pypebbles.http import HttpTransport
from pypebbles.http.drivers import Httpx

from apexdevkit.fastapi import RestfulServiceBuilder
from tests.fastapi.sample_api import setup


@pytest.fixture
def transport(service: RestfulServiceBuilder) -> HttpTransport:
    return Httpx(TestClient(setup(service.as_dependable())))
