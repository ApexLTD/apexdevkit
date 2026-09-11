from typing import Any

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository.core import Entity


class ContainsMixin:
    def __contains__(self, item: object) -> bool:
        match item:
            case Entity():
                return self.contains_id(item.id)
            case _:
                return False

    def contains_id(self, value: str) -> bool:
        try:
            self.read(value)
        except DoesNotExistError:
            return False

        return True

    def read(self, item_id: str) -> Any:
        raise NotImplementedError
