import pytest
from pypebbles import JsonDict
from pypebbles.runtime import Environment

from apexdevkit.http import Http, HttpMethod, Httpx

from .echo import Echo


@pytest.mark.vcr
def test_should_post(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.post, "post")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_submit(http: Httpx) -> None:
    form = JsonDict().with_a(Harry="Potter")
    response = http.with_data(form).request(HttpMethod.post, "post")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/x-www-form-urlencoded")
    echo.assert_form(expected=form)


@pytest.mark.vcr
def test_should_get(http: Httpx) -> None:
    response = http.request(HttpMethod.get, "get")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="get")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_get_with_params(http: Httpx) -> None:
    response = http.with_param("Color", "Yellow").request(HttpMethod.get, "get")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="get?Color=Yellow")


@pytest.mark.vcr
def test_should_patch(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.patch, "patch")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="patch")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_delete(http: Httpx) -> None:
    response = http.request(HttpMethod.delete, "delete")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="delete")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_put(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.put, "put")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="put")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.fixture
def http() -> Http:
    return (
        Httpx.Builder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .build()
        .with_header("User-Agent", "hogwarts")
    )
