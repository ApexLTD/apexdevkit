from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from pypebbles import JsonDict

from .domain import HttpMethod, HttpRequest


@dataclass(frozen=True)
class InternalEcho:
    _request: HttpRequest = field(default_factory=HttpRequest)

    def transport(self, request: HttpRequest) -> InternalEcho:
        return replace(self, _request=request)

    def over(self, method: HttpMethod) -> FakeResponse:
        return FakeResponse(
            content={
                "method": method.name,
                "endpoint": self._request.endpoint,
                "headers": self._request.headers,
                "params": self._request.params,
                "json": self._request.json,
                "data": self._request.data,
            }
        )


@dataclass(frozen=True)
class FakeResponse:
    content: Any = field(default_factory=dict)
    status_code: int = 200

    def raw(self) -> Any:
        return self.content

    def code(self) -> int:
        return self.status_code

    def json(self) -> Any:
        return JsonDict(self.content)

    def to[T](self, a_type: Callable[[FakeResponse], T]) -> T:
        return a_type(self)
