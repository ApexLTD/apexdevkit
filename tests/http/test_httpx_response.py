import pytest

from apexdevkit.http import FluentHttpResponse
from apexdevkit.http.fake import FakeResponse


class FakeHttpError(Exception):
    pass


def test_should_raise_on_bad_request() -> None:
    with pytest.raises(FakeHttpError):
        FluentHttpResponse(FakeResponse.bad_request()).on_bad_request(
            raises=FakeHttpError
        )


def test_should_raise_on_conflict() -> None:
    with pytest.raises(FakeHttpError):
        FluentHttpResponse(FakeResponse.conflict()).on_conflict(raises=FakeHttpError)


def test_should_raise_on_server_error() -> None:
    with pytest.raises(FakeHttpError) as cm:
        FluentHttpResponse(FakeResponse.fail()).on_failure(raises=FakeHttpError)

    assert str(cm.value) == "({}, 500)"


def test_should_raise_on_not_found() -> None:
    with pytest.raises(FakeHttpError):
        FluentHttpResponse(FakeResponse.not_found()).on_not_found(raises=FakeHttpError)


def test_should_respond_with_json() -> None:
    json = (
        FluentHttpResponse(FakeResponse())
        .on_bad_request(raises=AssertionError)
        .on_conflict(raises=AssertionError)
        .on_failure(raises=AssertionError)
        .json()
    )

    assert json == FakeResponse().json()
