from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

import pytest

from apexdevkit.http.domain import HttpResponse


class FakeHttpError(Exception):
    pass


def test_should_raise_on_bad_request() -> None:
    with pytest.raises(FakeHttpError):
        HttpResponse(status=400).on_bad_request(raises=FakeHttpError)


def test_should_raise_on_conflict() -> None:
    with pytest.raises(FakeHttpError):
        HttpResponse(status=409).on_conflict(raises=FakeHttpError)


def test_should_raise_on_server_error() -> None:
    with pytest.raises(FakeHttpError) as cm:
        HttpResponse(status=500).on_failure(raises=FakeHttpError)

    assert str(cm.value) == "(b'', 500)"


def test_should_raise_on_not_found() -> None:
    with pytest.raises(FakeHttpError):
        HttpResponse(status=404).on_not_found(raises=FakeHttpError)


def test_should_respond_with_json() -> None:
    apple = _Apple(name="Ambrosia", color="red")

    actual = (
        HttpResponse(status=200)
        .set_json(content=apple.dump())
        .on_bad_request(raises=AssertionError)
        .on_not_found(raises=AssertionError)
        .on_conflict(raises=AssertionError)
        .on_failure(raises=AssertionError)
        .load(using=_Apple.load)
    )

    assert actual == apple


@dataclass(frozen=True, kw_only=True)
class _Apple:
    name: str
    color: str

    @classmethod
    def load(cls, data: Mapping[str, Any]) -> "_Apple":
        return cls(name=data["name"], color=data["color"])

    def dump(self) -> Mapping[str, Any]:
        return asdict(self)
