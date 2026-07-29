from dataclasses import dataclass, replace
from unittest.mock import MagicMock

from apexdevkit.repository import Entity
from apexdevkit.sync import Sync
from apexdevkit.sync.source import SourceDiscriminator


@dataclass(frozen=True, kw_only=True)
class _Apple(Entity):
    name: str


def test_should_not_discriminate_the_same() -> None:
    items = [_Apple(name="Golden"), _Apple(name="Ambrosia")]

    source = SourceDiscriminator[_Apple](current=items, latest=items)

    assert list(source.absent()) == []
    assert list(source.new()) == []
    assert list(source.updates()) == []


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


def test_should_discriminate_within_sync() -> None:
    fuji = _Apple(name="fuji")
    gala = _Apple(name="Gala")
    golden = _Apple(name="Golden")
    target_mock = MagicMock()
    target_mock.__iter__.return_value = iter([gala, replace(fuji, name="Ambrosia")])

    (
        Sync[_Apple]()
        .discriminate(latest=[golden, fuji])
        .against(target=target_mock)
        .default()
        .run()
    )

    target_mock.prune.assert_called_once_with({gala})
    target_mock.load.assert_called_once_with({golden})
    target_mock.renew.assert_called_once_with({fuji})
