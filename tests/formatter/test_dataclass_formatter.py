from dataclasses import dataclass

from apexdevkit.formatter import DataclassFormatter


@dataclass
class SampleDataclass:
    name: str
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
        .with_nested(sample=DataclassFormatter(SampleDataclass))
        .and_nested(other_sample=DataclassFormatter(SampleDataclass))
        .dump(
            NestedDataclass(
                name="a",
                field=1,
                sample=SampleDataclass(name="b", field=2),
                other_sample=SampleDataclass(name="c", field=3),
            )
        )
    )

    assert result == {
        "name": "a",
        "field": 1,
        "sample": {"name": "b", "field": 2},
        "other_sample": {"name": "c", "field": 3},
    }


def test_should_load() -> None:
    result = (
        DataclassFormatter(NestedDataclass)
        .with_nested(sample=DataclassFormatter(SampleDataclass))
        .and_nested(other_sample=DataclassFormatter(SampleDataclass))
        .load(
            {
                "name": "a",
                "field": 1,
                "sample": {"name": "b", "field": 2},
                "other_sample": {"name": "c", "field": 3},
            }
        )
    )

    assert result == NestedDataclass(
        name="a",
        field=1,
        sample=SampleDataclass(name="b", field=2),
        other_sample=SampleDataclass(name="c", field=3),
    )
