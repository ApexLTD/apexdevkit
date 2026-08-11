from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from pypebbles import FluentDict, JsonDict

from apexdevkit.http.url import HttpUrl


@dataclass(frozen=True)
class HttpRequest:
    endpoint: str = ""
    headers: FluentDict[str] = field(default_factory=FluentDict[str])
    params: FluentDict[str] = field(default_factory=FluentDict[str])
    json: JsonDict | None = None
    data: JsonDict | None = None

    def with_endpoint(self, endpoint: str) -> HttpRequest:
        return replace(self, endpoint=HttpUrl(self.endpoint) + endpoint)

    def with_header(self, key: str, value: str) -> HttpRequest:
        return self.with_headers({key: value})

    def with_headers(self, value: Mapping[str, str]) -> HttpRequest:
        return replace(self, headers=self.headers.merge(FluentDict[str](value)))

    def with_param(self, key: str, value: str) -> HttpRequest:
        return self.with_params({key: value})

    def with_params(self, value: Mapping[str, str]) -> HttpRequest:
        return replace(self, params=self.params.merge(FluentDict[str](value)))

    def with_data(self, value: JsonDict) -> HttpRequest:
        return replace(self, data=value)

    def with_json(self, value: JsonDict) -> HttpRequest:
        return replace(self, json=value)
