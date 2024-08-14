from dataclasses import dataclass
from typing import Any

from apexdevkit.formatter import ListFormatter


@dataclass
class SampleClass:
    name: str
    age: int


@dataclass
class SampleClassFormatter:
    def load(self, raw: dict[str, Any]) -> SampleClass:
        return SampleClass(str(raw["name"]), int(raw["age"]))

    def dump(self, item: SampleClass) -> dict[str, Any]:
        return {"name": item.name, "age": item.age}


def test_should_dump() -> None:
    result = ListFormatter[SampleClass](SampleClassFormatter()).dump(
        [SampleClass("a", 1), SampleClass("b", 2)]
    )

    assert result == [{"name": "a", "age": 1}, {"name": "b", "age": 2}]


def test_should_load() -> None:
    result = ListFormatter[SampleClass](SampleClassFormatter()).load(
        [{"name": "a", "age": 1}, {"name": "b", "age": 2}]
    )

    assert result == [SampleClass("a", 1), SampleClass("b", 2)]


def test_should_retain_dumped_integrity() -> None:
    formatter = ListFormatter[SampleClass](SampleClassFormatter())

    dumped = formatter.dump([SampleClass("a", 1), SampleClass("b", 2)])
    formatter.load(dumped)

    assert dumped == [{"name": "a", "age": 1}, {"name": "b", "age": 2}]


def test_should_retain_loaded_integrity() -> None:
    formatter = ListFormatter[SampleClass](SampleClassFormatter())

    loaded = formatter.load([{"name": "a", "age": 1}, {"name": "b", "age": 2}])
    formatter.dump(loaded)

    assert loaded == [SampleClass("a", 1), SampleClass("b", 2)]
