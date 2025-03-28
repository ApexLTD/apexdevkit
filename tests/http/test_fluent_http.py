from apexdevkit.http import FakeHttp, FluentHttp, JsonDict
from apexdevkit.http.fluent import HttpMethod


def test_should_attach_headers() -> None:
    http = FakeHttp()

    FluentHttp(http).with_header("Harry", "Potter").and_header("Ronald", "Weasley")

    assert http.headers == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    http = FakeHttp()

    FluentHttp(http).with_param("Color", "Yellow").and_param("Shape", "Square")

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

    response = FluentHttp(http).post().on_endpoint(HttpMethod.post.name)

    assert response.json() == JsonDict()


def test_should_post_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).post().on_endpoint(HttpMethod.post.name)

    assert http.json == JsonDict()


def test_should_post_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).post().on_endpoint(HttpMethod.post.name)

    assert http.json == value


def test_should_post_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).post().on_endpoint(HttpMethod.post.name)

    assert http.data == value


def test_should_form_get_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).get().on_endpoint(HttpMethod.get.name)

    assert response.json() == JsonDict()


def test_should_get() -> None:
    http = FakeHttp()

    FluentHttp(http).get().on_endpoint(HttpMethod.get.name)

    http.intercepted(HttpMethod.get).on_endpoint(HttpMethod.get.name)


def test_should_form_patch_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).patch().on_endpoint(HttpMethod.patch.name)

    assert response.json() == JsonDict()


def test_should_patch_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).patch().on_endpoint(HttpMethod.patch.name)

    assert http.json == JsonDict()


def test_should_patch_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).patch().on_endpoint(HttpMethod.patch.name)

    assert http.json == value


def test_should_patch_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).patch().on_endpoint(HttpMethod.patch.name)

    assert http.data == value


def test_should_delete() -> None:
    http = FakeHttp()

    FluentHttp(http).delete().on_endpoint(HttpMethod.delete.name)

    http.intercepted(HttpMethod.delete).on_endpoint(HttpMethod.delete.name)


def test_should_form_delete_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).delete().on_endpoint(HttpMethod.delete.name)

    assert response.json() == JsonDict({})


def test_should_form_put_response() -> None:
    http = FakeHttp()

    response = FluentHttp(http).put().on_endpoint(HttpMethod.put.name)

    assert response.json() == JsonDict()


def test_should_put_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(http).put().on_endpoint(HttpMethod.put.name)

    assert http.json == JsonDict()


def test_should_put_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_json(value).put().on_endpoint(HttpMethod.put.name)

    assert http.json == value


def test_should_put_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(http).with_data(value).put().on_endpoint(HttpMethod.put.name)

    assert http.data == value
