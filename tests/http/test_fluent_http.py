from __future__ import annotations

from pypebbles import JsonDict

from apexdevkit.http import FluentHttp, HttpMethod
from apexdevkit.http.fake import InternalEcho
from tests.http.echo import Echo


def test_should_attach_headers() -> None:
    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_header("Harry", "Potter")
        .and_header("Ronald", "Weasley")
        .on_endpoint("get")
        .get()
        .json()
    )

    assert echo["headers"] == {"Harry": "Potter", "Ronald": "Weasley"}


def test_should_attach_params() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .with_param("Color", "Yellow")
        .and_param("Shape", "Square")
        .on_endpoint("get")
        .get()
        .load(Echo)
        .assert_endpoint(expected="get?Color=Yellow&Shape=Square")
    )


def test_should_attach_json() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_json(expected)
        .on_endpoint("post")
        .post()
        .json()
    )

    assert echo["json"] == expected


def test_should_attach_data() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_data(expected)
        .on_endpoint("post")
        .post()
        .json()
    )

    assert echo["form"] == expected


def test_should_form_post_response() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.post.name)
        .post()
        .load(Echo)
        .assert_endpoint(expected="post")
    )


def test_should_post_with_json() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_json(expected)
        .on_endpoint(HttpMethod.post.name)
        .post()
        .json()
    )

    assert echo["json"] == expected


def test_should_post_with_data() -> None:
    expected = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_data(expected)
        .on_endpoint(HttpMethod.post.name)
        .post()
        .json()
    )

    assert echo["form"] == expected


def test_should_form_get_response() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.get.name)
        .get()
        .load(Echo)
        .assert_endpoint(expected="get")
    )


def test_should_get() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.get.name)
        .get()
        .load(Echo)
        .assert_endpoint(expected="get")
    )


def test_should_form_patch_response() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .load(Echo)
        .assert_endpoint(expected="patch")
    )


def test_should_patch_with_json() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_json(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .json()
    )

    assert echo["json"] == value


def test_should_patch_with_data() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_data(value)
        .on_endpoint(HttpMethod.patch.name)
        .patch()
        .json()
    )

    assert echo["form"] == value


def test_should_delete() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.delete.name)
        .delete()
        .load(Echo)
        .assert_endpoint(expected="delete")
    )


def test_should_form_put_response() -> None:
    (
        FluentHttp(transporter=InternalEcho())
        .on_endpoint(HttpMethod.put.name)
        .put()
        .load(Echo)
        .assert_endpoint(expected="put")
    )


def test_should_put_with_json() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_json(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
        .json()
    )

    assert echo["json"] == value


def test_should_put_with_data() -> None:
    value = JsonDict().with_a(Harry="Potter")

    echo = (
        FluentHttp(transporter=InternalEcho())
        .with_data(value)
        .on_endpoint(HttpMethod.put.name)
        .put()
        .json()
    )

    assert echo["form"] == value
