import pytest
from pypebbles import JsonDict
from pypebbles.runtime import Environment

from apexdevkit.http import HttpMethod
from apexdevkit.http.domain import HttpRequest, HttpTransport
from apexdevkit.http.httpx.client import HttpxBuilder

from .echo import Echo


@pytest.mark.vcr
def test_should_post(transport: HttpTransport, a_json: JsonDict) -> None:
    (
        HttpRequest()
        .with_endpoint("post")
        .with_json(value=a_json)
        .using(transport)
        .post()
        .load(Echo)
        .assert_endpoint(expected="post")
        .assert_user_agent(expected="hogwarts")
        .assert_content_type(expected="application/json")
        .assert_json(expected=a_json)
    )


@pytest.mark.vcr
def test_should_submit(transport: HttpTransport, a_json: JsonDict) -> None:
    (
        HttpRequest()
        .with_endpoint("post")
        .with_data(value=a_json)
        .using(transport)
        .post()
        .load(Echo)
        .assert_endpoint(expected="post")
        .assert_user_agent(expected="hogwarts")
        .assert_content_type(expected="application/x-www-form-urlencoded")
        .assert_form(expected=a_json)
    )


@pytest.mark.vcr
def test_should_get(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("get")
        .using(transport)
        .dispatch(HttpMethod.get)
        .load(Echo)
        .assert_endpoint(expected="get")
        .assert_user_agent(expected="hogwarts")
    )


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
def test_should_patch(transport: HttpTransport, a_json: JsonDict) -> None:
    (
        HttpRequest()
        .with_endpoint("patch")
        .with_json(value=a_json)
        .using(transport)
        .patch()
        .load(Echo)
        .assert_endpoint(expected="patch")
        .assert_user_agent(expected="hogwarts")
        .assert_content_type(expected="application/json")
        .assert_json(expected=a_json)
    )


@pytest.mark.vcr
def test_should_delete(transport: HttpTransport) -> None:
    (
        HttpRequest()
        .with_endpoint("delete")
        .using(transport)
        .delete()
        .load(Echo)
        .assert_endpoint(expected="delete")
        .assert_user_agent(expected="hogwarts")
    )


@pytest.mark.vcr
def test_should_put(transport: HttpTransport, a_json: JsonDict) -> None:
    (
        HttpRequest()
        .with_endpoint("put")
        .with_json(value=a_json)
        .using(transport)
        .put()
        .load(Echo)
        .assert_endpoint(expected="put")
        .assert_user_agent(expected="hogwarts")
        .assert_content_type(expected="application/json")
        .assert_json(expected=a_json)
    )


@pytest.fixture
def transport() -> HttpTransport:
    return (
        HttpxBuilder()
        .with_url(Environment().value_of("ECHO_SERVER"))
        .with_header("User-Agent", "hogwarts")
        .transport()
    )


@pytest.fixture
def a_json() -> JsonDict:
    return JsonDict().with_a(Harry="Potter")
