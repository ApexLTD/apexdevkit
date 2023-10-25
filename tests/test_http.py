from typing import Any

import pytest
from pytest import fixture

from pydevtools.http import FluentHttpx, HttpUrl, Httpx, HttpxConfig

ECHO_SERVER = HttpUrl("http://httpbin.org")

JsonDict = dict[str, Any]


@fixture
def http() -> FluentHttpx:
    return FluentHttpx(Httpx(ECHO_SERVER, HttpxConfig().with_user_agent("hogwarts")))


@pytest.mark.vcr
def test_post(http: FluentHttpx) -> None:
    echo = (
        http.post()
        .with_json({"Harry": "Potter"})
        .on_endpoint("/post")
        .on_failure(
            raises=AssertionError,
        )
        .json()
    )

    assert echo.value_of("json").to(JsonDict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/post"
    assert echo.value_of("headers").to(JsonDict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(JsonDict)["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_get(http: FluentHttpx) -> None:
    echo = (
        http.get()
        .on_endpoint("/get")
        .on_failure(
            raises=AssertionError,
        )
        .json()
    )

    assert echo.value_of("args").to(JsonDict) == {}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get"
    assert echo.value_of("headers").to(JsonDict)["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_patch(http: FluentHttpx) -> None:
    echo = (
        http.patch()
        .with_json({"Harry": "Potter"})
        .on_endpoint("/patch")
        .on_failure(
            raises=AssertionError,
        )
        .json()
    )

    assert echo.value_of("json").to(JsonDict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/patch"
    assert echo.value_of("headers").to(JsonDict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(JsonDict)["Content-Type"] == "application/json"
