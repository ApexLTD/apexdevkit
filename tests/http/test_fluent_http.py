from pypebbles import JsonDict

from apexdevkit.http import FakeHttp, FluentHttp
from apexdevkit.http.fluent import HttpMethod


def test_should_attach_headers() -> None:
    http = FakeHttp()

    (
        FluentHttp(http)
        .with_header("Harry", "Potter")
        .and_header("Ronald", "Weasley")
        .on_endpoint("")
        .get()
    )

    assert http.headers == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    http = FakeHttp()

    (
        FluentHttp(http)
        .with_param("Color", "Yellow")
        .and_param("Shape", "Square")
        .on_endpoint("")
        .get()
    )

    assert http.params == {"Color": "Yellow", "Shape": "Square"}


def test_should_attach_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value)

    assert http.json == value


def test_should_attach_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value)

    assert http.data == value


def test_should_form_post_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).on_endpoint(HttpMethod.post.name).post()

    assert response.json() == JsonDict()


def test_should_post_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).on_endpoint(HttpMethod.post.name).post()

    assert http.json == JsonDict()


def test_should_post_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).on_endpoint(HttpMethod.post.name).post()

    assert http.json == value


def test_should_post_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).on_endpoint(HttpMethod.post.name).post()

    assert http.data == value


def test_should_form_get_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).on_endpoint(HttpMethod.get.name).get()

    assert response.json() == JsonDict()


def test_should_get() -> None:
    http = FakeHttp()

    FluentHttp(http).on_endpoint(HttpMethod.get.name).get()

    http.intercepted(HttpMethod.get).on_endpoint(HttpMethod.get.name)


def test_should_form_patch_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).on_endpoint(HttpMethod.patch.name).patch()

    assert response.json() == JsonDict()


def test_should_patch_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).on_endpoint(HttpMethod.patch.name).patch()

    assert http.json == JsonDict()


def test_should_patch_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).on_endpoint(HttpMethod.patch.name).patch()

    assert http.json == value


def test_should_patch_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).on_endpoint(HttpMethod.patch.name).patch()

    assert http.data == value


def test_should_delete() -> None:
    http = FakeHttp()

    FluentHttp(http).on_endpoint(HttpMethod.delete.name).delete()

    http.intercepted(HttpMethod.delete).on_endpoint(HttpMethod.delete.name)


def test_should_form_delete_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).on_endpoint(HttpMethod.delete.name).delete()

    assert response.json() == JsonDict({})


def test_should_form_put_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).on_endpoint(HttpMethod.put.name).put()

    assert response.json() == JsonDict()


def test_should_put_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).on_endpoint(HttpMethod.put.name).put()

    assert http.json == JsonDict()


def test_should_put_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).on_endpoint(HttpMethod.put.name).put()

    assert http.json == value


def test_should_put_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).on_endpoint(HttpMethod.put.name).put()

    assert http.data == value
