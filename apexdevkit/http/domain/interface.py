from __future__ import annotations

from typing import Protocol, Any

from pypebbles import JsonDict

from apexdevkit.http import HttpMethod
from apexdevkit.http.domain import HttpResponse


class Http(Protocol):  # pragma: no cover
    def with_endpoint(self, value: str) -> Http:
        pass

    def with_header(self, key: str, value: str) -> Http:
        pass

    def with_param(self, key: str, value: str) -> Http:
        pass

    def with_json(self, value: JsonDict) -> Http:
        pass

    def with_data(self, value: Any) -> Http:
        pass

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        pass
