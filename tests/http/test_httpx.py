import pytest
from pytest import fixture

from pydevtools.http import Http, Httpx, JsonDict

ECHO_SERVER = "http://httpbin.org"


@fixture
def http() -> Http:
    return Httpx.create_for(ECHO_SERVER).with_header("user-agent", "hogwarts")


@pytest.mark.vcr
def test_post(http: Httpx) -> None:
    response = http.post("/post", json=JsonDict().with_a(Harry="Potter"))

    echo = response.json()

    assert echo.value_of("json").to(dict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/post"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_get(http: Httpx) -> None:
    response = http.get("/get")

    echo = response.json()

    assert echo.value_of("args").to(dict) == {}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_patch(http: Httpx) -> None:
    response = http.patch("/patch", json=JsonDict().with_a(Harry="Potter"))

    echo = response.json()

    assert echo.value_of("json").to(dict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/patch"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_delete(http: Httpx) -> None:
    response = http.delete("/delete")

    echo = response.json()

    assert echo.value_of("args").to(dict) == {}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/delete"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
