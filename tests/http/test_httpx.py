from dataclasses import dataclass

import pytest

from apexdevkit.environment import environment_variable, value_of_env
from apexdevkit.http import Http, HttpMethod, Httpx, JsonDict


@pytest.mark.vcr
def test_should_post(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.post, "/post")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_submit(http: Httpx) -> None:
    form = JsonDict().with_a(Harry="Potter")
    response = http.with_data(form).request(HttpMethod.post, "/post")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/post")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/x-www-form-urlencoded")
    echo.assert_form(expected=form)


@pytest.mark.vcr
def test_should_get(http: Httpx) -> None:
    response = http.request(HttpMethod.get, "/get")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/get")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_get_with_params(http: Httpx) -> None:
    response = http.with_param("Color", "Yellow").request(HttpMethod.get, "/get")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/get?Color=Yellow")


@pytest.mark.vcr
def test_should_patch(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.patch, "/patch")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/patch")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.mark.vcr
def test_should_delete(http: Httpx) -> None:
    response = http.request(HttpMethod.delete, "/delete")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/delete")
    echo.assert_user_agent(expected="hogwarts")


@pytest.mark.vcr
def test_should_put(http: Httpx) -> None:
    json = JsonDict().with_a(Harry="Potter")
    response = http.with_json(json).request(HttpMethod.put, "/put")

    echo = Echo(response.json())
    echo.assert_endpoint(expected="/put")
    echo.assert_user_agent(expected="hogwarts")
    echo.assert_content_type(expected="application/json")
    echo.assert_json(expected=json)


@pytest.fixture
def http() -> Http:
    return (
        Httpx.Builder()
        .with_url(value_of_env(variable="ECHO_SERVER"))
        .build()
        .with_header("User-Agent", "hogwarts")
    )


@dataclass(frozen=True)
class Echo:
    raw: JsonDict

    server: str = environment_variable(
        name="ECHO_SERVER",
        default="http://localhost:8080",
    )

    def header(self, name: str) -> str:
        return str(self.raw.value_of("headers").to(dict)[name])

    def assert_endpoint(self, *, expected: str) -> None:
        assert self.url() == self.server + "/" + expected.strip("/")

    def url(self) -> str:
        return self.raw.value_of("url").to(str)

    def assert_user_agent(self, *, expected: str) -> None:
        assert self.user_agent() == expected

    def user_agent(self) -> str:
        return self.header(name="User-Agent")

    def assert_content_type(self, *, expected: str) -> None:
        assert self.content_type() == expected

    def content_type(self) -> str:
        return self.header(name="Content-Type")

    def assert_json(self, *, expected: JsonDict) -> None:
        assert self.json() == expected

    def json(self) -> JsonDict:
        return JsonDict(self.raw.value_of("json").to(dict))

    def assert_form(self, *, expected: JsonDict) -> None:
        assert self.form() == expected

    def form(self) -> JsonDict:
        return JsonDict(self.raw.value_of("form").to(dict))
