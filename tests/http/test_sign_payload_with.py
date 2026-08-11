from dataclasses import dataclass

import pytest
from pypebbles import JsonDict
from pypebbles.runtime import Environment

from apexdevkit.http import FluentHttp, Httpx, SignPayloadWith
from apexdevkit.security import Signature
from tests.http.echo import Echo


@dataclass(frozen=True)
class FakeAuthority:
    HEADER = "X-Header"

    def sign(self, message: str) -> Signature:
        return Signature(name=self.HEADER, value=message)

    def verify(self, message: str, signature: Signature) -> bool:
        raise NotImplementedError  # pragma: no cover


@pytest.fixture
def http() -> FluentHttp:
    return FluentHttp(
        Httpx.Builder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .before_request(SignPayloadWith(FakeAuthority()))
        .channel()
    )


@pytest.mark.vcr
def test_should_hook_post_method(http: FluentHttp) -> None:
    payload = JsonDict().with_a(body="content")

    echo = Echo(http.with_json(payload).on_endpoint("post").post().json())

    assert echo.header(FakeAuthority.HEADER) == '{"body":"content"}'
