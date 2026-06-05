from typing import Generic

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository.core import ItemT


class ContainsMixin(Generic[ItemT]):
    def __contains__(self, item: ItemT) -> bool:
        try:
            self.read(item.id)
        except DoesNotExistError:
            return False

        return True

    def read(self, item_id: str) -> ItemT:
        raise NotImplementedError
