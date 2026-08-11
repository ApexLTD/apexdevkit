from dataclasses import dataclass

import pytest
from httpx2 import Response
from pypebbles.runtime import Environment

from apexdevkit.http.domain import HttpRequest, HttpTransport
from apexdevkit.http.httpx.client import HttpxBuilder


@pytest.mark.vcr
def test_should_hook_get_method(transport: HttpTransport) -> None:
    with pytest.raises(ValueError, match="get"):
        HttpRequest().with_endpoint("get").using(transport).get()


@pytest.mark.vcr
def test_should_hook_post_method(transport: HttpTransport) -> None:
    with pytest.raises(ValueError, match="post"):
        HttpRequest().with_endpoint("post").using(transport).post()


@pytest.mark.vcr
def test_should_hook_patch_method(transport: HttpTransport) -> None:
    with pytest.raises(ValueError, match="patch"):
        HttpRequest().with_endpoint("patch").using(transport).patch()


@pytest.mark.vcr
def test_should_hook_delete_method(transport: HttpTransport) -> None:
    with pytest.raises(ValueError, match="delete"):
        HttpRequest().with_endpoint("delete").using(transport).delete()


@pytest.fixture
def transport() -> HttpTransport:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .with_header("User-Agent", "Hogwarts")
        .after_response(_Handler())
        .transport()
    )


@dataclass
class _Handler:
    def on_get(self, _: Response) -> None:
        raise ValueError("on_get")

    def on_post(self, _: Response) -> None:
        raise ValueError("on_post")

    def on_patch(self, _: Response) -> None:
        raise ValueError("on_patch")

    def on_delete(self, _: Response) -> None:
        raise ValueError("on_delete")
