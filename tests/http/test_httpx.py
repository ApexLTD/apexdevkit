import pytest

from apexdevkit.http import Http, HttpMethod, Httpx, JsonDict

ECHO_SERVER = "http://httpbin.org"


@pytest.fixture
def http() -> Http:
    return (
        Httpx.Builder()
        .with_url(ECHO_SERVER)
        .build()
        .with_header("User-Agent", "hogwarts")
    )


@pytest.mark.vcr
def test_should_post(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.post, "/post")

    echo = response.json().select("headers", "json", "url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/post"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"
    assert echo.value_of("json").to(dict) == json


@pytest.mark.vcr
def test_should_get(http: Httpx) -> None:
    response = http.request(HttpMethod.get, "/get")

    echo = response.json().select("headers", "json", "url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_should_get_with_params(http: Httpx) -> None:
    response = http.with_param("Color", "Yellow").request(HttpMethod.get, "/get")

    echo = response.json().select("url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/get?Color=Yellow"


@pytest.mark.vcr
def test_should_patch(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.patch, "/patch")

    echo = response.json().select("headers", "json", "url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/patch"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"
    assert echo.value_of("json").to(dict) == json


@pytest.mark.vcr
def test_should_delete(http: Httpx) -> None:
    response = http.request(HttpMethod.delete, "/delete")

    echo = response.json().select("headers", "json", "url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/delete"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"


@pytest.mark.vcr
def test_should_put(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.put, "/put")

    echo = response.json().select("headers", "json", "url")

    assert echo.value_of("url").to(str) == ECHO_SERVER + "/put"
    assert echo.value_of("headers").to(dict)["User-Agent"] == "hogwarts"
    assert echo.value_of("headers").to(dict)["Content-Type"] == "application/json"
    assert echo.value_of("json").to(dict) == json
