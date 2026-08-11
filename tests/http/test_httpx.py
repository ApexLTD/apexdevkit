import pytest
from pypebbles import JsonDict
from pypebbles.runtime import Environment

from apexdevkit.http import FluentHttp
from apexdevkit.http.httpx.client import HttpxBuilder

from .echo import Echo


@pytest.mark.vcr
def test_should_post(http: FluentHttp) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).on_endpoint("post").post()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_submit(http: FluentHttp) -> None:
    form = JsonDict().with_a(Harry="Potter")
    response = http.with_data(form).on_endpoint("post").post()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/x-www-form-urlencoded")
    echo.assert_form(expected=form)


@pytest.mark.vcr
def test_should_get(http: FluentHttp) -> None:
    response = http.on_endpoint("get").get()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="get")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_get_with_params(http: FluentHttp) -> None:
    response = http.with_param("Color", "Yellow").on_endpoint("get").get()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="get?Color=Yellow")


@pytest.mark.vcr
def test_should_patch(http: FluentHttp) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).on_endpoint("patch").patch()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="patch")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_delete(http: FluentHttp) -> None:
    response = http.on_endpoint("delete").delete()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="delete")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_put(http: FluentHttp) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).on_endpoint("put").put()

    echo = Echo(response.json())
    echo.assert_endpoint(expected="put")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.fixture
def http() -> FluentHttp:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .build()
        .with_header("User-Agent", "hogwarts")
    )
