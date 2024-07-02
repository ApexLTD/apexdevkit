from apexdevkit.http.url import HttpUrl


def test_should_not_add_trailing_stalsh_for_empty_endpoint() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "" == "https://www.example.com"


def test_httpurl_add_endpoint_to_value() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "test" == "https://www.example.com/test"


def test_httpurl_add_endpoint_to_value_with_trailing_slash() -> None:
    url = HttpUrl("https://www.example.com/")

    assert url + "test" == "https://www.example.com/test"


def test_httpurl_add_endpoint_with_leading_slash() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "/test" == "https://www.example.com/test"
