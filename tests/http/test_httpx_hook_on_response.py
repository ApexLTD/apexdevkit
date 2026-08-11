from dataclasses import dataclass

import pytest
from httpx2 import Response
from pypebbles.runtime import Environment

from apexdevkit.http import FluentHttp
from apexdevkit.http.httpx.client import HttpxBuilder


@pytest.fixture
def http() -> FluentHttp:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .after_response(FakeResponseHandler())
        .build()
        .with_header("User-Agent", "Hogwarts")
    )


@dataclass
class FakeResponseHandler:
    def on_get(self, _: Response) -> None:
        raise ValueError("on_get")

    def on_post(self, _: Response) -> None:
        raise ValueError("on_post")

    def on_patch(self, _: Response) -> None:
        raise ValueError("on_patch")

    def on_delete(self, _: Response) -> None:
        raise ValueError("on_delete")


@pytest.mark.vcr
def test_should_hook_get_method(http: FluentHttp) -> None:
    with pytest.raises(ValueError, match="get"):
        http.on_endpoint("get").get()


@pytest.mark.vcr
def test_should_hook_post_method(http: FluentHttp) -> None:
    with pytest.raises(ValueError, match="post"):
        http.on_endpoint("post").post()


@pytest.mark.vcr
def test_should_hook_patch_method(http: FluentHttp) -> None:
    with pytest.raises(ValueError, match="patch"):
        http.on_endpoint("patch").patch()


@pytest.mark.vcr
def test_should_hook_delete_method(http: FluentHttp) -> None:
    with pytest.raises(ValueError, match="delete"):
        http.on_endpoint("delete").delete()
