from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pypebbles import JsonDict


class HttpResponse(ABC):  # pragma: no cover
    @abstractmethod
    def code(self) -> int:
        pass

    @abstractmethod
    def raw(self) -> Any:
        pass

    @abstractmethod
    def json(self) -> JsonDict:
        pass

    def to[T](self, a_type: Callable[[HttpResponse], T]) -> T:
        return a_type(self)

    def on_bad_request(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.code() == 400:
            raise raises

        return self

    def on_conflict(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.code() == 409:
            raise raises

        return self

    def on_not_found(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.code() == 404:
            raise raises

        return self

    def on_failure(self, raises: type[Exception]) -> HttpResponse:
        if self.code() < 200 or self.code() > 299:
            raise raises(self.raw(), self.code())

        return self
