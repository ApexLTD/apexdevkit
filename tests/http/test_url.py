from apexdevkit.http.url import HttpUrl


def test_should_not_add_trailing_slash_for_empty_endpoint() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "" == "https://www.example.com"


def test_should_add_endpoint_to_base() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "test" == "https://www.example.com/test"


def test_should_add_endpoint_to_base_with_trailing_slash() -> None:
    url = HttpUrl("https://www.example.com/")

    assert url + "test" == "https://www.example.com/test"


def test_should_add_endpoint_with_leading_slash() -> None:
    url = HttpUrl("https://www.example.com")

    assert url + "/test" == "https://www.example.com/test"
