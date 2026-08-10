from __future__ import annotations

from dataclasses import dataclass, field, replace

from pypebbles import JsonDict

from apexdevkit.http.url import HttpUrl


@dataclass(frozen=True)
class HttpRequest:
    endpoint: str = ""
    headers: JsonDict = field(default_factory=JsonDict)
    params: JsonDict = field(default_factory=JsonDict)
    json: JsonDict | None = None
    data: JsonDict | None = None

    def with_endpoint(self, endpoint: str) -> HttpRequest:
        return replace(self, endpoint=HttpUrl(self.endpoint) + endpoint)

    def with_header(self, key: str, value: str) -> HttpRequest:
        return replace(self, headers=self.headers.merge(JsonDict({key: value})))

    def with_param(self, key: str, value: str) -> HttpRequest:
        return replace(self, params=self.params.merge(JsonDict({key: value})))

    def with_data(self, value: JsonDict) -> HttpRequest:
        return replace(self, data=value)

    def with_json(self, value: JsonDict) -> HttpRequest:
        return replace(self, json=value)
