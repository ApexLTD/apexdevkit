import pytest
from pypebbles import JsonDict
from pypebbles.runtime import Environment

from apexdevkit.http import HttpMethod
from apexdevkit.http.domain import HttpRequest, HttpTransport
from apexdevkit.http.httpx.client import HttpxBuilder

from .echo import Echo


@pytest.mark.vcr
def test_should_post(transport: HttpTransport) -> None:
    json = JsonDict().with_a(Harry="Potter")

    echo = (
        HttpRequest()
        .with_endpoint("post")
        .with_json(value=json)
        .using(transport)
        .post()
        .load(Echo)
    )

    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_submit(transport: HttpTransport) -> None:
    form = JsonDict().with_a(Harry="Potter")

    echo = (
        HttpRequest()
        .with_endpoint("post")
        .with_data(value=form)
        .using(transport)
        .post()
        .load(Echo)
    )

    echo.assert_endpoint(expected="post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/x-www-form-urlencoded")
    echo.assert_form(expected=form)


@pytest.mark.vcr
def test_should_get(transport: HttpTransport) -> None:
    echo = (
        HttpRequest()
        .with_endpoint("get")
        .using(transport)
        .dispatch(HttpMethod.get)
        .load(Echo)
    )

    echo.assert_endpoint(expected="get")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_get_with_params(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("get")
        .with_param("Color", "Yellow")
        .using(transport)
        .dispatch(HttpMethod.get)
        .load(Echo)
        .assert_endpoint(expected="get?Color=Yellow")
    )


@pytest.mark.vcr
def test_should_patch(transport: HttpTransport) -> None:
    json = JsonDict().with_a(Harry="Potter")

    echo = (
        HttpRequest()
        .with_endpoint("patch")
        .with_json(value=json)
        .using(transport)
        .patch()
        .load(Echo)
    )

    echo.assert_endpoint(expected="patch")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_delete(transport: HttpTransport) -> None:
    echo = HttpRequest().with_endpoint("delete").using(transport).delete().load(Echo)

    echo.assert_endpoint(expected="delete")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_put(transport: HttpTransport) -> None:
    json = JsonDict().with_a(Harry="Potter")

    echo = (
        HttpRequest()
        .with_endpoint("put")
        .with_json(value=json)
        .using(transport)
        .put()
        .load(Echo)
    )

    echo.assert_endpoint(expected="put")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.fixture
def transport() -> HttpTransport:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .with_header("User-Agent", "hogwarts")
        .transport()
    )
