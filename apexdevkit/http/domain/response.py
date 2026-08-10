from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from pypebbles import JsonDict


@dataclass(frozen=True)
class HttpResponse:  # pragma: no cover
    status: int

    content: bytes = b""

    def load[T](self, using: Callable[[JsonDict], T]) -> T:
        return using(self.json())

    def json(self) -> JsonDict:
        return JsonDict(json.loads(self.content))

    def set_json(self, content: Mapping[str, Any]) -> HttpResponse:
        return HttpResponse(self.status, json.dumps(content).encode())

    def on_bad_request(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.status == 400:
            raise raises

        return self

    def on_conflict(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.status == 409:
            raise raises

        return self

    def on_not_found(self, raises: Exception | type[Exception]) -> HttpResponse:
        if self.status == 404:
            raise raises

        return self

    def on_failure(self, raises: type[Exception]) -> HttpResponse:
        if self.status < 200 or self.status > 299:
            raise raises(self.content, self.status)

        return self
