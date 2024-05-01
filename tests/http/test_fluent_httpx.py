from pydevtools.http import FakeHttp, FluentHttp, JsonDict


def test_should_attach_headers() -> None:
    http = FakeHttp()

    FluentHttp(http).with_header("Harry", "Potter").and_header("Ronald", "Weasley")

    assert http.headers == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    http = FakeHttp()

    FluentHttp(http).with_param("Color", "Yellow").and_param("Shape", "Square")

    assert http.params == {"Color": "Yellow", "Shape": "Square"}


def test_should_form_post_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).post().on_endpoint("/post")

    assert response.json() == JsonDict()


def test_should_post_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).post().on_endpoint("/post")

    http.request.assert_post().with_json(JsonDict()).on_endpoint("/post")


def test_should_post_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).post().with_json(value).on_endpoint("/post")

    http.request.assert_post().with_json(value).on_endpoint("/post")


def test_should_form_get_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).get().on_endpoint("/get")

    assert response.json() == JsonDict()


def test_should_form_patch_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).patch().on_endpoint("/patch")

    assert response.json() == JsonDict()


def test_should_patch_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).patch().on_endpoint("/patch")

    http.request.assert_patch().with_json(JsonDict()).on_endpoint("/patch")


def test_should_patch_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).patch().with_json(value).on_endpoint("/patch")

    http.request.assert_patch().with_json(value).on_endpoint("/patch")


def test_should_form_delete_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).delete().on_endpoint("/delete")

    assert response.json() == JsonDict({})
