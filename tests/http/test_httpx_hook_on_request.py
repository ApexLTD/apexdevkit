from dataclasses import dataclass

import pytest
from httpx2 import Request
from pypebbles.runtime import Environment

from apexdevkit.http import FluentHttp, HttpMethod
from apexdevkit.http.httpx.client import HttpxBuilder
from tests.http.echo import Echo

ECHO_SERVER = Environment().value_of("ECHO_SERVER")


@pytest.fixture
def http() -> FluentHttp:
    return (
        HttpxBuilder()
        .with_url(ECHO_SERVER)
        .before_request(FakeRequestHandler())
        .build()
    )


@dataclass
class FakeRequestHandler:
    name: str = "Handler"

    def on_get(self, request: Request) -> None:
        request.headers[self.name] = "on_get"

    def on_post(self, request: Request) -> None:
        request.headers[self.name] = "on_post"

    def on_patch(self, request: Request) -> None:
        request.headers[self.name] = "on_patch"

    def on_delete(self, request: Request) -> None:
        request.headers[self.name] = "on_delete"


@pytest.mark.vcr
def test_should_hook_get_method(http: FluentHttp) -> None:
    response = http.on_endpoint("get").dispatch(HttpMethod.get)

    echo = Echo(response.json())
    assert echo.header(name="Handler") == "on_get"


@pytest.mark.vcr
def test_should_hook_post_method(http: FluentHttp) -> None:
    response = http.on_endpoint("post").dispatch(HttpMethod.post)

    echo = Echo(response.json())
    assert echo.header(name="Handler") == "on_post"


@pytest.mark.vcr
def test_should_hook_patch_method(http: FluentHttp) -> None:
    response = http.on_endpoint("patch").dispatch(HttpMethod.patch)

    echo = Echo(response.json())
    assert echo.header(name="Handler") == "on_patch"


@pytest.mark.vcr
def test_should_hook_delete_method(http: FluentHttp) -> None:
    response = http.on_endpoint("delete").dispatch(HttpMethod.delete)

    echo = Echo(response.json())
    assert echo.header(name="Handler") == "on_delete"
