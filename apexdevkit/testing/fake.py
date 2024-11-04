from __future__ import annotations

import random
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generic, Type, TypeVar

from faker import Faker

from apexdevkit.http import JsonDict
from apexdevkit.value import Value

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class Fake:
    faker: Faker = field(default_factory=Faker)

    def uuid(self) -> str:
        return str(self.faker.uuid4())

    def text(self, *, length: int) -> str:
        return "".join(self.faker.random_letters(length=length))

    def number(self, top: int = 100000) -> int:
        return int(self.faker.random.randint(0, top))

    def timestamp(self) -> int:
        return int(self.faker.unix_time())

    def minute(self) -> int:
        return int(self.faker.random_int(min=0, max=59))

    def hour(self) -> int:
        return int(self.faker.random_int(min=0, max=23))

    def first_name(self) -> str:
        return str(self.faker.first_name())

    def last_name(self) -> str:
        return str(self.faker.last_name())

    def sentence(self, *, words: int) -> str:
        return str(self.faker.sentence(nb_words=words))

    def country(self) -> str:
        return str(self.faker.country())

    def address(self) -> str:
        return str(self.faker.address())

    def bool(self) -> bool:
        return bool(self.faker.boolean())


@dataclass(frozen=True)
class FakeResource(Generic[ItemT]):
    item_type: Type[ItemT] = field()
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


@dataclass(frozen=True)
class FakeValue(FakeResource[Value]):
    item_type: Type[Value] = field(default=Value)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "value": self.fake.number(),
            "exponent": random.choice([10, 100, 1000]),
        }
