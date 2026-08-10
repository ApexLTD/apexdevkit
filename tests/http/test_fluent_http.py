from __future__ import annotations

from dataclasses import dataclass, field, replace

from pypebbles import JsonDict

from apexdevkit.http import FakeHttp, FluentHttp, Http, HttpMethod
from apexdevkit.http.domain import HttpRequest, HttpResponse


def test_should_attach_headers() -> None:
    http = FakeHttp()

    (
        FluentHttp(channel=FakeChannel(http))
        .with_header("Harry", "Potter")
        .and_header("Ronald", "Weasley")
        .on_endpoint("")
        .get()
    )

    assert http.headers == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    http = FakeHttp()

    (
        FluentHttp(channel=FakeChannel(http))
        .with_param("Color", "Yellow")
        .and_param("Shape", "Square")
        .on_endpoint("")
        .get()
    )

    assert http.params == {"Color": "Yellow", "Shape": "Square"}


def test_should_attach_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(channel=FakeChannel(http)).with_json(value).on_endpoint("").post()

    assert http.json == value


def test_should_attach_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    FluentHttp(channel=FakeChannel(http)).with_data(value).on_endpoint("").post()

    assert http.data == value


def test_should_form_post_response() -> None:
    http = FakeHttp()

    response = (
        FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.post.name).post()
    )

    assert response.json() == JsonDict()


def test_should_post_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.post.name).post()

    assert http.json == JsonDict()


def test_should_post_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_json(value)
        .on_endpoint(HttpMethod.post.name)
        .post()
    )

    assert http.json == value


def test_should_post_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_data(value)
        .on_endpoint(HttpMethod.post.name)
        .post()
    )

    assert http.data == value


def test_should_form_get_response() -> None:
    http = FakeHttp()

    response = (
        FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.get.name).get()
    )

    assert response.json() == JsonDict()


def test_should_get() -> None:
    http = FakeHttp()

    FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.get.name).get()

    http.intercepted(HttpMethod.get).on_endpoint(HttpMethod.get.name)


def test_should_form_patch_response() -> None:
    http = FakeHttp()

    response = (
        FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.patch.name).patch()
    )

    assert response.json() == JsonDict()


def test_should_patch_with_defaults() -> None:
    http = FakeHttp()

    (FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.patch.name).patch())

    assert http.json == JsonDict()


def test_should_patch_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_json(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
    )

    assert http.json == value


def test_should_patch_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_data(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
    )

    assert http.data == value


def test_should_delete() -> None:
    http = FakeHttp()

    (FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.delete.name).delete())

    http.intercepted(HttpMethod.delete).on_endpoint(HttpMethod.delete.name)


def test_should_form_delete_response() -> None:
    http = FakeHttp()

    response = (
        FluentHttp(channel=FakeChannel(http))
        .on_endpoint(HttpMethod.delete.name)
        .delete()
    )

    assert response.json() == JsonDict({})


def test_should_form_put_response() -> None:
    http = FakeHttp()

    response = (
        FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.put.name).put()
    )

    assert response.json() == JsonDict()


def test_should_put_with_defaults() -> None:
    http = FakeHttp()

    FluentHttp(channel=FakeChannel(http)).on_endpoint(HttpMethod.put.name).put()

    assert http.json == JsonDict()


def test_should_put_with_json() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_json(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
    )

    assert http.json == value


def test_should_put_with_data() -> None:
    http = FakeHttp()
    value = JsonDict().with_a(Harry="Potter")

    (
        FluentHttp(channel=FakeChannel(http))
        .with_data(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
    )

    assert http.data == value


@dataclass(frozen=True)
class FakeChannel:
    http: Http

    _request: HttpRequest = field(default_factory=HttpRequest)

    def transport(self, request: HttpRequest) -> FakeChannel:
        return replace(self, _request=request)

    def over(self, method: HttpMethod) -> HttpResponse:
        http = self.http

        for key, value in self._request.headers.items():
            http = http.with_header(key, value)

        for key, value in self._request.params.items():
            http = http.with_param(key, value)

        if self._request.data is not None:
            http = http.with_data(self._request.data)

        if self._request.json is not None:
            http = http.with_json(self._request.json)

        return http.request(method, endpoint=self._request.endpoint)
