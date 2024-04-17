import pytest
from pytest import fixture

from pydevtools.http import HttpUrl, Httpx, HttpxConfig

ECHO_SERVER = HttpUrl("http://httpbin.org")


@fixture
def http() -> Httpx:
    return Httpx(ECHO_SERVER, HttpxConfig().with_user_agent("hogwarts"))


@pytest.mark.vcr
def test_post(http: Httpx) -> None:
    response = http.post("/post", json={"Harry": "Potter"})

    echo = response.json()

    assert echo["json"] == {"Harry": "Potter"}
    assert echo["url"] == ECHO_SERVER + "/post"
    assert echo["headers"]["User-Agent"] == "hogwarts"
    assert echo["headers"]["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_post_with_header(http: Httpx) -> None:
    response = http.post("/post", json={"Harry": "Potter"}, headers={"Key": "Value"})

    echo = response.json()

    assert echo["json"] == {"Harry": "Potter"}
    assert echo["url"] == ECHO_SERVER + "/post"
    assert echo["headers"]["User-Agent"] == "hogwarts"
    assert echo["headers"]["Key"] == "Value"
    assert echo["headers"]["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_get(http: Httpx) -> None:
    response = http.get("/get")

    echo = response.json()

    assert echo["args"] == {}
    assert echo["url"] == ECHO_SERVER + "/get"
    assert echo["headers"]["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_get_with_params(http: Httpx) -> None:
    response = http.get("/get", params={"color": "yellow"})

    echo = response.json()

    assert echo["args"] == {"color": "yellow"}
    assert echo["url"] == ECHO_SERVER + "/get?color=yellow"
    assert echo["headers"]["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_patch(http: Httpx) -> None:
    response = http.patch("/patch", json={"Harry": "Potter"})

    echo = response.json()

    assert echo["json"] == {"Harry": "Potter"}
    assert echo["url"] == ECHO_SERVER + "/patch"
    assert echo["headers"]["User-Agent"] == "hogwarts"
    assert echo["headers"]["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_delete(http: Httpx) -> None:
    response = http.delete("/delete")

    echo = response.json()

    assert echo["args"] == {}
    assert echo["url"] == ECHO_SERVER + "/delete"
    assert echo["headers"]["User-Agent"] == "hogwarts"
