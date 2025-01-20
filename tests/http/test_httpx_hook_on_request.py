from dataclasses import dataclass

import httpx
import pytest

from apexdevkit.http import HttpMethod, Httpx

ECHO_SERVER = "http://httpbin.org"


@pytest.fixture
def http() -> Httpx:
    return (
        Httpx.Builder()
        .with_url(ECHO_SERVER)
        .before_request(FakeRequestHandler())
        .build()
    )


@dataclass
class FakeRequestHandler:
    name: str = "Handler"

    def on_get(self, request: httpx.Request) -> None:
        request.headers[self.name] = "on_get"

    def on_post(self, request: httpx.Request) -> None:
        request.headers[self.name] = "on_post"

    def on_patch(self, request: httpx.Request) -> None:
        request.headers[self.name] = "on_patch"

    def on_delete(self, request: httpx.Request) -> None:
        request.headers[self.name] = "on_delete"


@pytest.mark.vcr
def test_should_hook_get_method(http: Httpx) -> None:
    response = http.request(HttpMethod.get, "/get")

    headers = response.json().value_of("headers").as_dict()

    assert headers["Handler"] == "on_get"


@pytest.mark.vcr
def test_should_hook_post_method(http: Httpx) -> None:
    response = http.request(HttpMethod.post, "/post")

    headers = response.json().value_of("headers").as_dict()

    assert headers["Handler"] == "on_post"


@pytest.mark.vcr
def test_should_hook_patch_method(http: Httpx) -> None:
    response = http.request(HttpMethod.patch, "/patch")

    headers = response.json().value_of("headers").as_dict()

    assert headers["Handler"] == "on_patch"


@pytest.mark.vcr
def test_should_hook_delete_method(http: Httpx) -> None:
    response = http.request(HttpMethod.delete, "/delete")

    headers = response.json().value_of("headers").as_dict()

    assert headers["Handler"] == "on_delete"
