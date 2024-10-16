from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from apexdevkit.http.fluent import HttpMethod, HttpResponse
from apexdevkit.http.json import JsonDict


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

    @classmethod
    def bad_request(cls) -> FakeResponse:
        return FakeResponse(status_code=400)

    @classmethod
    def conflict(cls) -> FakeResponse:
        return FakeResponse(status_code=409)

    @classmethod
    def fail(cls) -> FakeResponse:
        return FakeResponse(status_code=500)

    @classmethod
    def not_found(cls) -> FakeResponse:
        return FakeResponse(status_code=404)


@dataclass
class FakeHttp:
    response: FakeResponse = field(default_factory=FakeResponse)

    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    json: JsonDict = field(default_factory=JsonDict)

    _request: InterceptedRequest = field(init=False)

    def with_endpoint(self, value: str) -> Self:  # pragma: no cover
        raise NotImplementedError

    def with_header(self, key: str, value: str) -> Self:
        self.headers[key] = value

        return self

    def with_param(self, key: str, value: str) -> Self:
        self.params[key] = value

        return self

    def with_json(self, value: JsonDict) -> Self:
        self.json = value

        return self

    def request(self, method: HttpMethod, endpoint: str = "") -> HttpResponse:
        self._request = InterceptedRequest(method, endpoint)

        return self.response

    def intercepted(self, method: HttpMethod) -> InterceptedRequest:
        assert self._request.method == method

        return self._request


@dataclass
class InterceptedRequest:
    method: HttpMethod
    endpoint: str

    def on_endpoint(self, value: str) -> None:
        assert self.endpoint == value
