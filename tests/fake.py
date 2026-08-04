from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from faker import Faker

from apexdevkit.http import JsonDict


@dataclass(frozen=True)
class Fake:
    faker: Faker = field(default_factory=Faker)

    def uuid(self) -> str:
        return str(self.faker.uuid4())

    def text(self, *, length: int) -> str:
        return "".join(self.faker.random_letters(length=length))

    def number(self, top: int = 100000) -> int:
        return int(self.faker.random.randint(0, top))

    def boolean(self) -> bool:
        return bool(self.faker.boolean())


@dataclass(frozen=True)
class FakeResource[ItemT]:
    item_type: type[ItemT] = field()
    fake: Fake = field(default_factory=Fake)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {}

    def unknown_id(self) -> str:
        return self.fake.text(length=32)

    def json(self) -> JsonDict:
        return JsonDict(self._raw)

    def entity(self, **fields: Any) -> ItemT:
        return self.item_type(**self.json().merge(JsonDict(fields)))
