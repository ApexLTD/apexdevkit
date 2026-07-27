from dataclasses import dataclass, replace

from apexdevkit.repository import Entity
from apexdevkit.sync.source import SourceDiscriminator


@dataclass(frozen=True, kw_only=True)
class _Apple(Entity):
    name: str


def test_should_discriminate_removals() -> None:
    current = [_Apple(name="Golden"), _Apple(name="Ambrosia")]

    source = SourceDiscriminator[_Apple](current=current, latest=[current[0]])

    assert list(source.absent()) == [current[1]]


def test_should_discriminate_additions() -> None:
    latest = [_Apple(name="Golden"), _Apple(name="Ambrosia")]

    source = SourceDiscriminator[_Apple](current=[latest[0]], latest=latest)

    assert list(source.new()) == [latest[1]]


def test_should_discriminate_changes() -> None:
    current = [_Apple(name="Golden"), _Apple(name="Ambrosia")]
    latest = [current[0], replace(current[1], name="Ambrosia (Malus domestica)")]

    source = SourceDiscriminator[_Apple](current=current, latest=latest)

    assert list(source.updates()) == [latest[1]]
    assert list(source.absent()) == []
    assert list(source.new()) == []
