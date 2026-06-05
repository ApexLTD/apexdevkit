from typing import Generic

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository.core import Entity, ItemT


class ContainsMixin(Generic[ItemT]):
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

    def read(self, item_id: str) -> ItemT:
        raise NotImplementedError
