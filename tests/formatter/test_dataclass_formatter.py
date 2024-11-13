from __future__ import annotations

from dataclasses import dataclass, field

from apexdevkit.formatter import DataclassFormatter, ListFormatter


@dataclass
class Name:
    name: str
    ordering: int


@dataclass
class SampleDataclass:
    name: Name
    field: int


@dataclass
class NestedDataclass:
    name: str
    field: int
    sample: SampleDataclass
    other_sample: SampleDataclass


@dataclass
class NestedListDataclass:
    name: str
    field: int
    samples: list[SampleDataclass]
    primitives: list[int]
    map: dict[str, str]


@dataclass
class SampleNoneDataclass:
    name: str
    count: int | None = field(default=3)
    sample: SampleDataclass | None = None
    samples: list[SampleDataclass] | None = field(default_factory=list)


def test_should_dump() -> None:
    result = DataclassFormatter(NestedDataclass).dump(
        NestedDataclass(
            name="a",
            field=1,
            sample=SampleDataclass(name=Name("b", 1), field=2),
            other_sample=SampleDataclass(name=Name("c", 1), field=3),
        )
    )

    assert result == {
        "name": "a",
        "field": 1,
        "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
        "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
    }


def test_should_load() -> None:
    result = DataclassFormatter(NestedDataclass).load(
        {
            "name": "a",
            "field": 1,
            "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
            "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
        }
    )

    assert result == NestedDataclass(
        name="a",
        field=1,
        sample=SampleDataclass(name=Name("b", 1), field=2),
        other_sample=SampleDataclass(name=Name("c", 1), field=3),
    )


def test_should_retain_dumped_integrity() -> None:
    formatter = (
        DataclassFormatter(NestedDataclass)
        .with_nested(
            sample=DataclassFormatter(SampleDataclass).with_nested(
                name=DataclassFormatter(Name)
            )
        )
        .and_nested(
            other_sample=DataclassFormatter(SampleDataclass).with_nested(
                name=DataclassFormatter(Name)
            )
        )
    )

    dumped = formatter.dump(
        NestedDataclass(
            name="a",
            field=1,
            sample=SampleDataclass(name=Name("b", 1), field=2),
            other_sample=SampleDataclass(name=Name("c", 1), field=3),
        )
    )
    formatter.load(dumped)

    assert dumped == {
        "name": "a",
        "field": 1,
        "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
        "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
    }


def test_should_retain_loaded_integrity() -> None:
    formatter = DataclassFormatter(NestedDataclass)

    loaded = formatter.load(
        {
            "name": "a",
            "field": 1,
            "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
            "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
        }
    )
    formatter.dump(loaded)

    assert loaded == NestedDataclass(
        name="a",
        field=1,
        sample=SampleDataclass(name=Name("b", 1), field=2),
        other_sample=SampleDataclass(name=Name("c", 1), field=3),
    )


def test_should_retain_nested_empty_list_on_dump() -> None:
    item = NestedListDataclass("a", field=1, samples=[], primitives=[1], map={"0": "0"})

    result = DataclassFormatter(NestedListDataclass).dump(item)

    assert result == {
        "name": "a",
        "field": 1,
        "samples": [],
        "primitives": [1],
        "map": {"0": "0"},
    }


def test_should_retain_nested_empty_list_on_load() -> None:
    result = DataclassFormatter(NestedListDataclass).load(
        {
            "name": "a",
            "field": 1,
            "samples": [],
            "primitives": [1],
            "map": {"0": "0"},
        }
    )

    assert result == NestedListDataclass(
        name="a", field=1, samples=[], primitives=[1], map={"0": "0"}
    )


def test_should_load_with_list() -> None:
    result = DataclassFormatter(NestedListDataclass).load(
        {
            "name": "a",
            "field": 1,
            "samples": [{"name": {"name": "b", "ordering": 1}, "field": 1}],
            "primitives": [1],
            "map": {"0": "0"},
        }
    )

    assert result == NestedListDataclass(
        name="a",
        field=1,
        samples=[SampleDataclass(name=Name("b", 1), field=1)],
        primitives=[1],
        map={"0": "0"},
    )


def test_should_load_nested_formatter_with_list() -> None:
    result = (
        DataclassFormatter(NestedListDataclass)
        .with_nested(samples=ListFormatter(DataclassFormatter(SampleDataclass)))
        .load(
            {
                "name": "a",
                "field": 1,
                "samples": [{"name": {"name": "b", "ordering": 1}, "field": 1}],
                "primitives": [1],
                "map": {"0": "0"},
            }
        )
    )

    assert result == NestedListDataclass(
        name="a",
        field=1,
        samples=[SampleDataclass(name=Name("b", 1), field=1)],
        primitives=[1],
        map={"0": "0"},
    )


def test_should_assign_default_to_nonexistent_keys() -> None:
    result = DataclassFormatter(SampleNoneDataclass).load(
        {
            "name": "a",
        }
    )

    assert result == SampleNoneDataclass(
        name="a",
        count=3,
        sample=None,
        samples=[],
    )
