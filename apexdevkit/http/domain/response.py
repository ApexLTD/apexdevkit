from __future__ import annotations

from typing import Any, Protocol

from pypebbles import JsonDict


class HttpResponse(Protocol):  # pragma: no cover
    def code(self) -> int:
        pass

    def raw(self) -> Any:
        pass

    def json(self) -> JsonDict:
        pass

    def to[T](self, a_type: type[T]) -> T:
        pass
