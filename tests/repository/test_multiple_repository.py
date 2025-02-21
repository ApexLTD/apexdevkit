from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from pytest import fixture

from apexdevkit.formatter import DataclassFormatter, PickleFormatter
from apexdevkit.repository import InMemoryByteStore, InMemoryRepository, Repository
from apexdevkit.repository.repository import (
    MultipleRepositoryBuilder,
)


@dataclass(frozen=True)
class Animal:
    id: str
    type: AnimalType
    name: str
    age: int


class AnimalType(str, Enum):
    bird = "bird"
    fish = "fish"


@dataclass(frozen=True)
class AnimalFormatter:
    def dump(self, animal: Animal) -> bytes:
        return PickleFormatter[Mapping[str, Any]]().dump(
            {
                "id": int(animal.id),
                "type": animal.type.value,
                "name": animal.name,
                "age": animal.age,
            }
        )

    def load(self, data: bytes) -> Animal:
        raw = PickleFormatter[Mapping[str, Any]]().load(data)
        return Animal(
            str(raw["id"]),
            AnimalType[raw["type"]],
            (raw["name"]),
            int(raw["age"]),
        )


@dataclass(frozen=True)
class BirdFormatter:
    def dump(self, animal: Animal) -> Animal:
        raw = dict(deepcopy(DataclassFormatter(Animal).dump(animal)))
        raw["id"] = raw["id"].replace("bird_", "")
        return Animal(**raw)

    def load(self, animal: Animal) -> Animal:
        raw = dict(deepcopy(DataclassFormatter(Animal).dump(animal)))
        raw["id"] = "bird_" + raw["id"]
        return Animal(**raw)


@dataclass(frozen=True)
class FishFormatter:
    def dump(self, animal: Animal) -> Animal:
        raw = dict(deepcopy(DataclassFormatter(Animal).dump(animal)))
        raw["id"] = raw["id"].replace("fish_", "")
        return Animal(**raw)

    def load(self, animal: Animal) -> Animal:
        raw = dict(deepcopy(DataclassFormatter(Animal).dump(animal)))
        raw["id"] = "fish_" + raw["id"]
        return Animal(**raw)


@fixture
def birds() -> Repository[Animal]:
    return (
        InMemoryRepository[Animal]()
        .with_store(InMemoryByteStore[Animal](formatter=AnimalFormatter()))
        .build()
    )


@fixture
def fishes() -> Repository[Animal]:
    return (
        InMemoryRepository[Animal]()
        .with_store(InMemoryByteStore[Animal](formatter=AnimalFormatter()))
        .build()
    )


@fixture
def multiple(
    birds: Repository[Animal], fishes: Repository[Animal]
) -> Repository[Animal]:
    return (
        MultipleRepositoryBuilder[Animal]()
        .with_repository(
            birds,
            condition=lambda animal: animal.type == AnimalType.bird,
            formatter=BirdFormatter(),
            id_prefix="bird_",
        )
        .and_repository(
            fishes,
            condition=lambda animal: animal.type == AnimalType.fish,
            formatter=FishFormatter(),
            id_prefix="fish_",
        )
        .build()
    )


def test_should_count_all(
    birds: Repository[Animal], fishes: Repository[Animal], multiple: Repository[Animal]
) -> None:
    bird = Animal(id="1", type=AnimalType.bird, name="Bird", age=1)
    fish = Animal(id="2", type=AnimalType.fish, name="Fish", age=1)

    birds.create(bird)
    fishes.create(fish)

    assert len(multiple) == 2


def test_should_retrieve_all(
    birds: Repository[Animal], fishes: Repository[Animal], multiple: Repository[Animal]
) -> None:
    bird = Animal(id="1", type=AnimalType.bird, name="Bird", age=1)
    fish = Animal(id="2", type=AnimalType.fish, name="Fish", age=1)

    birds.create(bird)
    fishes.create(fish)

    assert set(multiple) == {
        Animal(id="bird_1", type=AnimalType.bird, name="Bird", age=1),
        Animal(id="fish_2", type=AnimalType.fish, name="Fish", age=1),
    }


def test_should_create(
    birds: Repository[Animal], fishes: Repository[Animal], multiple: Repository[Animal]
) -> None:
    bird = Animal(id="bird_1", type=AnimalType.bird, name="Bird", age=1)

    created = multiple.create(bird)

    assert created == bird
    assert list(birds) == [Animal(id="1", type=AnimalType.bird, name="Bird", age=1)]
    assert len(fishes) == 0


def test_should_read(birds: Repository[Animal], multiple: Repository[Animal]) -> None:
    bird = Animal(id="bird_1", type=AnimalType.bird, name="Bird", age=1)
    birds.create(Animal(id="1", type=AnimalType.bird, name="Bird", age=1))

    value = multiple.read(bird.id)

    assert value == bird


def test_should_update(birds: Repository[Animal], multiple: Repository[Animal]) -> None:
    bird = Animal(id="bird_1", type=AnimalType.bird, name="Bird", age=1)
    birds.create(Animal(id="1", type=AnimalType.bird, name="Bird", age=1))

    updated = Animal(id="bird_1", type=AnimalType.bird, name="Bird", age=2)
    multiple.update(updated)

    assert birds.read(bird.id.removeprefix("bird_")) == Animal(
        "1", type=AnimalType.bird, name="Bird", age=2
    )


def test_should_delete(birds: Repository[Animal], multiple: Repository[Animal]) -> None:
    bird = Animal(id="1", type=AnimalType.bird, name="Bird", age=1)
    birds.create(bird)

    multiple.delete("bird_" + bird.id)

    assert len(birds) == 0
