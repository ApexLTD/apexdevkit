from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self
from unittest.mock import MagicMock


@dataclass
class FakeHttp:
    response: Any = field(default_factory=MagicMock)

    request: InterceptedRequest = field(init=False)

    def post(
        self, endpoint: str, json: dict[str, Any], headers: dict[str, Any] | None = None
    ) -> Any:
        self.request = InterceptedRequest(
            method="post",
            endpoint=endpoint,
            json=json,
            headers=headers,
        )

        return self.response

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        self.request = InterceptedRequest(
            method="get",
            endpoint=endpoint,
            params=params,
        )

        return self.response

    def patch(self, endpoint: str, json: dict[str, Any]) -> Any:
        self.request = InterceptedRequest(
            method="patch",
            endpoint=endpoint,
            json=json,
        )

        return self.response

    def delete(self, endpoint: str) -> Any:
        self.request = InterceptedRequest(method="delete", endpoint=endpoint)

        return self.response


@dataclass
class InterceptedRequest:
    method: str
    endpoint: str

    json: Any = field(default_factory=object)
    headers: Any = field(default_factory=object)
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

    def with_headers(self, value: Any) -> Self:
        assert self.headers == value

        return self

    def with_params(self, value: Any) -> Self:
        assert self.params == value

        return self

    def on_endpoint(self, value: str) -> Self:
        assert self.endpoint == value

        return self
