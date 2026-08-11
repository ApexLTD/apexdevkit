from dataclasses import dataclass
from typing import Self

from pypebbles import JsonDict
from pypebbles.runtime import Environment


@dataclass(frozen=True)
class Echo:
    raw: JsonDict

    server: str = Environment().inject(
        variable="ECHO_SERVER",
        default="http://localhost:8080",
    )

    def assert_header(self, name: str, value: str) -> Self:
        assert self.header(name=name) == value

        return self

    def header(self, name: str) -> str:
        return str(self.raw.value_of("headers").to(dict)[name])

    def assert_endpoint(self, *, expected: str) -> Self:
        assert self.raw.value_of("url").to(str) == self._url_for(expected)

        return self

    def _url_for(self, endpoint: str) -> str:
        return self.server + "/" + endpoint.strip("/")

    def assert_user_agent(self, *, expected: str) -> Self:
        assert self.header(name="User-Agent") == expected

        return self

    def assert_content_type(self, *, expected: str) -> Self:
        assert self.header(name="Content-Type") == expected

        return self

    def assert_json(self, *, expected: JsonDict) -> Self:
        assert self._sub_object_of(key="json") == expected

        return self

    def assert_form(self, *, expected: JsonDict) -> Self:
        assert self._sub_object_of(key="form") == expected

        return self

    def _sub_object_of(self, key: str) -> JsonDict:
        return JsonDict(self.raw.value_of(key).to(dict))
