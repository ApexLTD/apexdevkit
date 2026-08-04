from dataclasses import dataclass
from typing import Any

from apexdevkit.environment import environment_variable
from apexdevkit.fluent import FluentDict
from apexdevkit.http import JsonDict


@dataclass(frozen=True)
class Echo:
    raw: JsonDict

    server: str = environment_variable(
        name="ECHO_SERVER",
        default="http://localhost:8080",
    )

    def header(self, name: str) -> str:
        return str(self.raw.value_of("headers").to(dict)[name])

    def assert_endpoint(self, *, expected: str) -> None:
        assert self.raw.value_of("url").to(str) == self._url_for(expected)

    def _url_for(self, endpoint: str) -> str:
        return self.server + "/" + endpoint.strip("/")

    def assert_user_agent(self, *, expected: str) -> None:
        assert self.header(name="User-Agent") == expected

    def assert_content_type(self, *, expected: str) -> None:
        assert self.header(name="Content-Type") == expected

    def assert_json(self, *, expected: JsonDict) -> None:
        assert self._sub_object_of(key="json") == expected

    def assert_form(self, *, expected: JsonDict) -> None:
        assert self._sub_object_of(key="form") == expected

    def _sub_object_of(self, key: str) -> FluentDict[Any]:
        return JsonDict(self.raw.value_of(key).to(dict))
