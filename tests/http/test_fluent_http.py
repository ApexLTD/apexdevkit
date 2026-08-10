from __future__ import annotations

from pypebbles import JsonDict

from apexdevkit.http import FluentHttp, HttpMethod
from apexdevkit.http.fake import InternalEcho


def test_should_attach_headers() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .with_header("Harry", "Potter")
        .and_header("Ronald", "Weasley")
        .on_endpoint("")
        .get()
        .json()
    )

    assert echo["headers"] == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .with_param("Color", "Yellow")
        .and_param("Shape", "Square")
        .on_endpoint("")
        .get()
        .json()
    )

    assert echo["params"] == {"Color": "Yellow", "Shape": "Square"}


def test_should_attach_json() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_json(expected)
        .on_endpoint("")
        .post()
        .json()
    )

    assert echo["json"] == expected


def test_should_attach_data() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_data(expected)
        .on_endpoint("")
        .post()
        .json()
    )

    assert echo["data"] == expected


def test_should_form_post_response() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .on_endpoint(HttpMethod.post.name)
        .post()
        .json()
    )

    assert echo == (
        JsonDict()
        .with_a(method="post")
        .and_a(endpoint="post")
        .and_a(headers={})
        .and_a(params={})
        .and_a(json=None)
        .and_a(data=None)
    )


def test_should_post_with_json() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_json(expected)
        .on_endpoint(HttpMethod.post.name)
        .post()
        .json()
    )

    assert echo["json"] == expected


def test_should_post_with_data() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_data(expected)
        .on_endpoint(HttpMethod.post.name)
        .post()
        .json()
    )

    assert echo["data"] == expected


def test_should_form_get_response() -> None:
    echo = (
        FluentHttp(channel=InternalEcho()).on_endpoint(HttpMethod.get.name).get().json()
    )

    assert echo == (
        JsonDict()
        .with_a(method="get")
        .and_a(endpoint="get")
        .and_a(headers={})
        .and_a(params={})
        .and_a(json=None)
        .and_a(data=None)
    )


def test_should_get() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .on_endpoint(HttpMethod.get.name)
        .get()
        .json()
        .select("method", "endpoint")
    )

    assert echo == {"method": "get", "endpoint": "get"}


def test_should_form_patch_response() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .json()
    )

    assert echo == (
        JsonDict()
        .with_a(method="patch")
        .and_a(endpoint="patch")
        .and_a(headers={})
        .and_a(params={})
        .and_a(json=None)
        .and_a(data=None)
    )


def test_should_patch_with_json() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_json(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .json()
    )

    assert echo["json"] == value


def test_should_patch_with_data() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_data(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .json()
    )

    assert echo["data"] == value


def test_should_delete() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .on_endpoint(HttpMethod.delete.name)
        .delete()
        .json()
        .select("method", "endpoint")
    )

    assert echo == {"method": "delete", "endpoint": "delete"}


def test_should_form_delete_response() -> None:
    echo = (
        FluentHttp(channel=InternalEcho())
        .on_endpoint(HttpMethod.delete.name)
        .delete()
        .json()
    )

    assert echo == (
        JsonDict()
        .with_a(method="delete")
        .and_a(endpoint="delete")
        .and_a(headers={})
        .and_a(params={})
        .and_a(json=None)
        .and_a(data=None)
    )


def test_should_form_put_response() -> None:
    echo = (
        FluentHttp(channel=InternalEcho()).on_endpoint(HttpMethod.put.name).put().json()
    )

    assert echo == (
        JsonDict()
        .with_a(method="put")
        .and_a(endpoint="put")
        .and_a(headers={})
        .and_a(params={})
        .and_a(json=None)
        .and_a(data=None)
    )


def test_should_put_with_json() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_json(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
        .json()
    )

    assert echo["json"] == value


def test_should_put_with_data() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(channel=InternalEcho())
        .with_data(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
        .json()
    )

    assert echo["data"] == value
