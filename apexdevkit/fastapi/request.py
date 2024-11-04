from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apexdevkit.http import Http, HttpMethod, JsonDict
from apexdevkit.http.fluent import HttpResponse


@dataclass
class HttpRequest:
    method: HttpMethod
    http: Http

    def with_endpoint(self, value: Any) -> HttpRequest:
        self.http = self.http.with_endpoint(str(value))

        return self

    def with_param(self, name: str, value: Any) -> HttpRequest:
        self.http = self.http.with_param(name, value)

        return self

    def with_json(self, value: JsonDict) -> HttpRequest:
        self.http = self.http.with_json(value)

        return self

    def __call__(self) -> HttpResponse:
        return self.http.request(self.method)
