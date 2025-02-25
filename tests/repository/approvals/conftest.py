from dataclasses import dataclass, field
from uuid import uuid4

from pytest import fixture


@dataclass
class Apple:
    color: str
    parent: str | None

    id: str = field(default_factory=lambda: str(uuid4()))


@fixture
def apple() -> Apple:
    return Apple(color="red", parent="test", id="1")
