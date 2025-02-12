from __future__ import annotations

from dataclasses import dataclass

import pytest

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter


@dataclass
class _Person:
    id: str
    name: str
    amount: int


_PersonFormatter = AliasFormatter[_Person]


@pytest.fixture
def formatter() -> _PersonFormatter:
    return AliasFormatter(
        DataclassFormatter(_Person),
        alias=AliasMapping.parse(id="ID", name="Name"),
    )


def test_should_dump_with_alias(formatter: _PersonFormatter) -> None:
    person = _Person(id="1", name="orion", amount=10)

    assert formatter.dump(person) == {"ID": "1", "Name": "orion", "amount": 10}


def test_should_load_without_alias(formatter: _PersonFormatter) -> None:
    raw = {"ID": "1", "Name": "orion", "amount": 10}

    assert formatter.load(raw) == _Person(id="1", name="orion", amount=10)
