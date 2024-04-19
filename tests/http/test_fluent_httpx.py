from pydevtools.http.fake import FakeHttp
from pydevtools.http.httpx import FluentHttp, HttpxResponse


def test_should_attach_headers() -> None:
    http = FakeHttp()

    FluentHttp(http).with_header("Harry", "Potter").and_header("Ronald", "Weasley")

    assert http.headers == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_form_post_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).post().on_endpoint("/post")

    assert response == HttpxResponse(http.response)


def test_should_post_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).post().on_endpoint("/post")

    http.request.assert_post().with_json({}).on_endpoint("/post")


def test_should_post_with_json() -> None:
    http = FakeHttp()

    FluentHttp(http).post().with_json({"Harry": "Potter"}).on_endpoint("/post")

    http.request.assert_post().with_json({"Harry": "Potter"}).on_endpoint("/post")


def test_should_form_get_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).get().on_endpoint("/get")

    assert response == HttpxResponse(http.response)


def test_should_get_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).get().on_endpoint("/get")

    http.request.assert_get().with_params({}).on_endpoint("/get")


def test_should_get_with_params() -> None:
    http = FakeHttp()

    FluentHttp(http).get().with_params(color="yellow").on_endpoint("/get")

    http.request.assert_get().with_params({"color": "yellow"}).on_endpoint("/get")


def test_should_form_patch_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).patch().on_endpoint("/patch")

    assert response == HttpxResponse(http.response)


def test_should_patch_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).patch().on_endpoint("/patch")

    http.request.assert_patch().with_json({}).on_endpoint("/patch")


def test_should_patch_with_json() -> None:
    http = FakeHttp()

    FluentHttp(http).patch().with_json({"Harry": "Potter"}).on_endpoint("/patch")

    http.request.assert_patch().with_json({"Harry": "Potter"}).on_endpoint("/patch")


def test_should_form_delete_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).delete().on_endpoint("/delete")

    assert response == HttpxResponse(http.response)


def test_should_delete_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).delete().on_endpoint("/delete")

    http.request.assert_delete().on_endpoint("/delete")
