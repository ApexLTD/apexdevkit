from __future__ import annotations

import warnings
from dataclasses import dataclass

import pytest

from pydevtools.annotation import deprecated


@deprecated("Do not use this class")
class OldClass:
    def __init__(self) -> None:
        self.data = 5


def test_should_warn_deprecated_class() -> None:
    with pytest.warns(DeprecationWarning, match=r"Do not use this class"):
        OldClass()


@dataclass
class Class:
    data: int

    @classmethod
    @deprecated("Do not use this class method")
    def create(cls) -> Class:
        return cls(0)

    def method(self) -> None:
        pass

    @deprecated("Do not use this method")
    def deprecated_method(self) -> None:
        pass

    @property
    @deprecated("Do not use this property")
    def property(self) -> int:
        return self.data + 1


def test_should_warn_deprecated_class_method() -> None:
    with pytest.warns(DeprecationWarning, match=r"Do not use this class method"):
        Class.create()


def test_should_warn_deprecated_method() -> None:
    with pytest.warns(DeprecationWarning, match=r"Do not use this method"):
        Class(0).deprecated_method()


def test_should_not_warn_regular_method() -> None:
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        Class(0).method()

    assert not warning_records


def test_should_warn_deprecated_property() -> None:
    with pytest.warns(DeprecationWarning, match=r"Do not use this property"):
        Class(Class(0).property)


@deprecated("Do not use this function")
def deprecated_function() -> None:
    pass


def test_should_warn_deprecated_function() -> None:
    with pytest.warns(DeprecationWarning, match=r"Do not use this function"):
        deprecated_function()
