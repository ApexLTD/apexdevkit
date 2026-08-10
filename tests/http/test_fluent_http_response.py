import pytest

from apexdevkit.http import FluentHttpResponse
from apexdevkit.http.fake import FakeResponse


class FakeHttpError(Exception):
    pass


def test_should_raise_on_bad_request() -> None:
    with pytest.raises(FakeHttpError):
        (
            FakeResponse(status_code=400)
            .to(FluentHttpResponse)
            .on_bad_request(raises=FakeHttpError)
        )


def test_should_raise_on_conflict() -> None:
    with pytest.raises(FakeHttpError):
        (
            FakeResponse(status_code=409)
            .to(FluentHttpResponse)
            .on_conflict(raises=FakeHttpError)
        )


def test_should_raise_on_server_error() -> None:
    with pytest.raises(FakeHttpError) as cm:
        (
            FakeResponse(status_code=500)
            .to(FluentHttpResponse)
            .on_failure(raises=FakeHttpError)
        )

    assert str(cm.value) == "({}, 500)"


def test_should_raise_on_not_found() -> None:
    with pytest.raises(FakeHttpError):
        (
            FakeResponse(status_code=404)
            .to(FluentHttpResponse)
            .on_not_found(raises=FakeHttpError)
        )


def test_should_respond_with_json() -> None:
    expected = {"Harry": "Potter"}

    actual = (
        FakeResponse(content=expected)
        .to(FluentHttpResponse)
        .on_bad_request(raises=AssertionError)
        .on_not_found(raises=AssertionError)
        .on_conflict(raises=AssertionError)
        .on_failure(raises=AssertionError)
        .json()
    )

    assert actual == expected
