from __future__ import annotations

from dataclasses import dataclass

from apexdevkit.formatter import DataclassFormatter


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


def test_should_dump() -> None:
    result = (
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
        .dump(
            NestedDataclass(
                name="a",
                field=1,
                sample=SampleDataclass(name=Name("b", 1), field=2),
                other_sample=SampleDataclass(name=Name("c", 1), field=3),
            )
        )
    )

    assert result == {
        "name": "a",
        "field": 1,
        "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
        "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
    }


def test_should_load() -> None:
    result = (
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
        .load(
            {
                "name": "a",
                "field": 1,
                "sample": {"name": {"name": "b", "ordering": 1}, "field": 2},
                "other_sample": {"name": {"name": "c", "ordering": 1}, "field": 3},
            }
        )
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
