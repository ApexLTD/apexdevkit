from dataclasses import dataclass

import pytest

from apexdevkit.environment import value_of_env
from apexdevkit.http import HttpMethod, Httpx, JsonDict, SignPayloadWith
from apexdevkit.security import Signature


@dataclass(frozen=True)
class FakeAuthority:
    HEADER = "X-Header"

    def sign(self, message: str) -> Signature:
        return Signature(name=self.HEADER, value=message)

    def verify(self, message: str, signature: Signature) -> bool:
        return signature.value == message


@pytest.fixture
def http() -> Httpx:
    return (
        Httpx.Builder()
        .with_url(value_of_env(variable="ECHO_SERVER"))
        .before_request(SignPayloadWith(FakeAuthority()))
        .build()
    )


@pytest.mark.vcr(
    match_on=[
        "method",
        "scheme",
        "host",
        "port",
        "path",
        "query",
        "headers",
    ]
)
def test_should_hook_post_method(http: Httpx) -> None:
    payload = JsonDict().with_a(body="content")

    headers = (
        http.with_json(payload)
        .request(HttpMethod.post, "/post")
        .json()
        .value_of("headers")
        .as_dict()
    )

    assert headers[FakeAuthority.HEADER] == '{"body":"content"}'
