from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self
from unittest.mock import MagicMock

from pydevtools.http.httpx import HttpResponse, HttpxResponse


@dataclass
class FakeHttp:
    response: HttpResponse = field(default_factory=MagicMock)

    request: InterceptedRequest = field(init=False)
    headers: dict[str, str] = field(default_factory=dict)

    def with_header(self, key: str, value: str) -> Self:
        self.headers[key] = value

        return self

    def post(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        self.request = InterceptedRequest(method="post", endpoint=endpoint, json=json)

        return HttpxResponse(self.response)

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> HttpxResponse:
        self.request = InterceptedRequest(
            method="get",
            endpoint=endpoint,
            params=params,
        )

        return HttpxResponse(self.response)

    def patch(self, endpoint: str, json: dict[str, Any]) -> HttpxResponse:
        self.request = InterceptedRequest(
            method="patch",
            endpoint=endpoint,
            json=json,
        )

        return HttpxResponse(self.response)

    def delete(self, endpoint: str) -> HttpxResponse:
        self.request = InterceptedRequest(method="delete", endpoint=endpoint)

        return HttpxResponse(self.response)


@dataclass
class InterceptedRequest:
    method: str
    endpoint: str

    json: Any = field(default_factory=object)
    params: Any = field(default_factory=object)

    def assert_post(self) -> Self:
        assert self.method == "post"

        return self

    def assert_get(self) -> Self:
        assert self.method == "get"

        return self

    def assert_patch(self) -> Self:
        assert self.method == "patch"

        return self

    def assert_delete(self) -> Self:
        assert self.method == "delete"

        return self

    def with_json(self, value: Any) -> Self:
        assert self.json == value

        return self

    def with_params(self, value: Any) -> Self:
        assert self.params == value

        return self

    def on_endpoint(self, value: str) -> Self:
        assert self.endpoint == value

        return self
