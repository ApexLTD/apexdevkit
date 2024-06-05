from dataclasses import dataclass, field

from faker import Faker


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
