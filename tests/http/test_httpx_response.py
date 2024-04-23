import pytest

from pydevtools.http import FluentHttpResponse
from pydevtools.http.fake import FakeResponse


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
    with pytest.raises(FakeHttpError):
        FluentHttpResponse(FakeResponse.fail()).on_failure(raises=FakeHttpError)


def test_should_respond_with_json() -> None:
    json = (
        FluentHttpResponse(FakeResponse())
        .on_bad_request(raises=AssertionError)
        .on_conflict(raises=AssertionError)
        .on_failure(raises=AssertionError)
        .json()
    )

    assert json == FakeResponse().json()
