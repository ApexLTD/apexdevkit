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
        .after_response(FakeResponseHandler())
        .build()
        .with_header("User-Agent", "Hogwarts")
    )


@dataclass
class FakeResponseHandler:
    def on_get(self, _: httpx.Response) -> None:
        raise ValueError("on_get")

    def on_post(self, _: httpx.Response) -> None:
        raise ValueError("on_post")

    def on_patch(self, _: httpx.Response) -> None:
        raise ValueError("on_patch")

    def on_delete(self, _: httpx.Response) -> None:
        raise ValueError("on_delete")


@pytest.mark.vcr
def test_should_hook_get_method(http: Httpx) -> None:
    with pytest.raises(ValueError, match="get"):
        http.request(HttpMethod.get, "/get")


@pytest.mark.vcr
def test_should_hook_post_method(http: Httpx) -> None:
    with pytest.raises(ValueError, match="post"):
        http.request(HttpMethod.post, "/post")


@pytest.mark.vcr
def test_should_hook_patch_method(http: Httpx) -> None:
    with pytest.raises(ValueError, match="patch"):
        http.request(HttpMethod.patch, "/patch")


@pytest.mark.vcr
def test_should_hook_delete_method(http: Httpx) -> None:
    with pytest.raises(ValueError, match="delete"):
        http.request(HttpMethod.delete, "/delete")
