from dataclasses import dataclass

import pytest

from apexdevkit.repository import Entity


@dataclass(frozen=True, kw_only=True)
class Apple(Entity):
    color: str
    parent: str | None


@pytest.fixture
def apple() -> Apple:
    return Apple(color="red", parent="test", id="1")
