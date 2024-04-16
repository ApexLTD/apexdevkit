import pytest
from pytest import fixture

from pydevtools.http import FluentHttpx, HttpUrl, Httpx, HttpxConfig

ECHO_SERVER = HttpUrl("http://httpbin.org")


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

    assert echo.value_of("json").to(dict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/post"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_post_with_header(http: FluentHttpx) -> None:
    echo = (
        http.post()
        .with_json({"Harry": "Potter"})
        .and_header("Key", "Value")
        .on_endpoint("/post")
        .on_failure(
            raises=AssertionError,
        )
        .json()
    )

    assert echo.value_of("json").to(dict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/post"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Key"] == "Value"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"


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

    assert echo.value_of("args").to(dict) == {}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_get_with_params(http: FluentHttpx) -> None:
    echo = (
        http.get()
        .with_params(color="yellow")
        .on_endpoint("/get")
        .on_failure(raises=AssertionError)
        .json()
    )

    assert echo.value_of("args").to(dict) == {"color": "yellow"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get?color=yellow"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


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

    assert echo.value_of("json").to(dict) == {"Harry": "Potter"}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/patch"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"


@pytest.mark.vcr
def test_delete(http: FluentHttpx) -> None:
    echo = (
        http.delete()
        .on_endpoint("/delete")
        .on_failure(
            raises=AssertionError,
        )
        .json()
    )

    assert echo.value_of("args").to(dict) == {}
    assert echo.value_of("url").to(str) == ECHO_SERVER + "/delete"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


class ConflictError(Exception):
    pass


class BadRequestError(Exception):
    pass


class ServerError(Exception):
    pass


@pytest.mark.vcr
def test_bad_request(http: FluentHttpx) -> None:
    with pytest.raises(BadRequestError):
        (
            http.get()
            .on_endpoint("/status/400")
            .on_bad_request(raises=BadRequestError)
            .on_failure(raises=ServerError)
        )


@pytest.mark.vcr
def test_on_conflict(http: FluentHttpx) -> None:
    with pytest.raises(ConflictError):
        (
            http.get()
            .on_endpoint("/status/409")
            .on_conflict(raises=ConflictError)
            .on_failure(raises=ServerError)
        )


@pytest.mark.vcr
def test_server_error(http: FluentHttpx) -> None:
    with pytest.raises(ServerError):
        (
            http.get()
            .on_endpoint("/status/500")
            .on_bad_request(raises=BadRequestError)
            .on_failure(raises=ServerError)
        )
