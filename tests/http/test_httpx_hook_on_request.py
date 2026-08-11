from dataclasses import dataclass

import pytest
from httpx2 import Request
from pypebbles.runtime import Environment

from apexdevkit.http import HttpMethod
from apexdevkit.http.domain import HttpRequest, HttpTransport
from apexdevkit.http.httpx.client import HttpxBuilder
from tests.http.echo import Echo


@pytest.mark.vcr
def test_should_hook_get_method(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("get")
        .using(transport)
        .dispatch(HttpMethod.get)
        .load(Echo)
        .assert_header(name="Handler", value="on_get")
    )


@pytest.mark.vcr
def test_should_hook_post_method(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("post")
        .using(transport)
        .dispatch(HttpMethod.post)
        .load(Echo)
        .assert_header(name="Handler", value="on_post")
    )


@pytest.mark.vcr
def test_should_hook_patch_method(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("patch")
        .using(transport)
        .dispatch(HttpMethod.patch)
        .load(Echo)
        .assert_header(name="Handler", value="on_patch")
    )


@pytest.mark.vcr
def test_should_hook_delete_method(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("delete")
        .using(transport)
        .dispatch(HttpMethod.delete)
        .load(Echo)
        .assert_header(name="Handler", value="on_delete")
    )


@pytest.fixture
def transport() -> HttpTransport:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .before_request(_Handler())
        .transport()
    )


@dataclass(frozen=True)
class _Handler:
    name: str = "Handler"

    def on_get(self, request: Request) -> None:
        request.headers[self.name] = "on_get"

    def on_post(self, request: Request) -> None:
        request.headers[self.name] = "on_post"

    def on_patch(self, request: Request) -> None:
        request.headers[self.name] = "on_patch"

    def on_delete(self, request: Request) -> None:
        request.headers[self.name] = "on_delete"
