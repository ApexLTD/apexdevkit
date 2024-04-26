from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from pydevtools.http.fluent import HttpResponse
from pydevtools.http.json import JsonDict


@dataclass
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


@dataclass
class FakeHttp:
    response: FakeResponse = field(default_factory=FakeResponse)

    request: InterceptedRequest = field(init=False)
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)

    def with_header(self, key: str, value: str) -> Self:
        self.headers[key] = value

        return self

    def with_param(self, key: str, value: str) -> Self:
        self.params[key] = value

        return self

    def post(self, endpoint: str, json: JsonDict) -> HttpResponse:
        self.request = InterceptedRequest(method="post", endpoint=endpoint, json=json)

        return self.response

    def get(self, endpoint: str) -> HttpResponse:
        self.request = InterceptedRequest(
            method="get",
            endpoint=endpoint,
            params=self.params,
        )

        return self.response

    def patch(self, endpoint: str, json: JsonDict) -> HttpResponse:
        self.request = InterceptedRequest(
            method="patch",
            endpoint=endpoint,
            json=json,
        )

        return self.response

    def delete(self, endpoint: str) -> HttpResponse:
        self.request = InterceptedRequest(method="delete", endpoint=endpoint)

        return self.response


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

    def with_json(self, value: JsonDict) -> Self:
        assert self.json == value

        return self

    def with_params(self, value: Any) -> Self:
        assert self.params == value

        return self

    def on_endpoint(self, value: str) -> Self:
        assert self.endpoint == value

        return self
