from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generic, Type, TypeVar

from faker import Faker

from apexdevkit.http import JsonDict

ItemT = TypeVar("ItemT")


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def uuid(self) -> str:
        return str(self.faker.uuid4())

    def text(self, *, length: int) -> str:
        return "".join(self.faker.random_letters(length=length))

    def number(self) -> int:
        return int(self.faker.random.randint(0, 100000))

    def timestamp(self) -> int:
        return int(self.faker.unix_time())

    def minute(self) -> int:
        return int(self.faker.random_int(min=0, max=59))

    def hour(self) -> int:
        return int(self.faker.random_int(min=0, max=23))


@dataclass
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
