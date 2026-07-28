from apexdevkit.repository import BruteForceBatch, InMemoryRepository
from apexdevkit.sync import Sync
from tests.repository.data import AppleItem


def test() -> None:
    repository = BruteForceBatch(
        inner=InMemoryRepository[AppleItem]()
        .with_seeded(AppleItem(color="Red"))
        .and_seeded(AppleItem(color="Green"))
        .and_seeded(AppleItem(color="Blue"))
    )

    Sync[AppleItem]().purge(repository)

    assert len(repository) == 0
    assert list(repository) == []
