from dataclasses import dataclass, field
from uuid import uuid4

import pytest


@dataclass
class Apple:
    color: str
    parent: str | None

    id: str = field(default_factory=lambda: str(uuid4()))


@pytest.fixture
def apple() -> Apple:
    return Apple(color="red", parent="test", id="1")
