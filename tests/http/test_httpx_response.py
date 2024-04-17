from unittest.mock import MagicMock

import pytest

from pydevtools.http import JsonObject
from pydevtools.http.httpx import HttpxResponse


class FakeHttpError(Exception):
    pass


def test_should_raise_on_bad_request() -> None:
    with pytest.raises(FakeHttpError):
        HttpxResponse(MagicMock(status_code=400)).on_bad_request(raises=FakeHttpError)


def test_should_raise_on_conflict() -> None:
    with pytest.raises(FakeHttpError):
        HttpxResponse(MagicMock(status_code=409)).on_conflict(raises=FakeHttpError)


def test_should_raise_on_server_error() -> None:
    with pytest.raises(FakeHttpError):
        HttpxResponse(MagicMock(status_code=500)).on_failure(raises=FakeHttpError)


def test_should_respond_with_json() -> None:
    response = MagicMock(status_code=200)

    json = (
        HttpxResponse(response)
        .on_bad_request(raises=AssertionError)
        .on_conflict(raises=AssertionError)
        .on_failure(raises=AssertionError)
        .json()
    )

    assert json == JsonObject(response.json())
