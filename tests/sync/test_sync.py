from typing import Any
from unittest.mock import MagicMock

import pytest
from faker import Faker

from apexdevkit.sync import Source, SourceFailing, SourcePreSet, Sync, TargetFailing


def test_should_not_prune(source: Source[Any]) -> None:
    Sync(
        source=SourceFailing.on_absent(using=source),
        target=TargetFailing.on_prune(),
    ).run(prune=False)


def test_should_not_load(source: Source[Any]) -> None:
    Sync(
        source=SourceFailing.on_new(using=source),
        target=TargetFailing.on_load(),
    ).run(load=False)


def test_should_not_update(source: Source[Any]) -> None:
    Sync(
        source=SourceFailing.on_update(using=source),
        target=TargetFailing.on_update(),
    ).run(update=False)


def test_should_dry_run(source: Source[Any]) -> None:
    Sync(source=source, target=TargetFailing.on_everything(), dry_run=True).run()


def test_should_run_all(source: Source[Any]) -> None:
    target = MagicMock()

    Sync(source=source, target=target).run(prune=True, load=True, update=True)

    target.prune.assert_called_once_with(source.absent())
    target.load.assert_called_once_with(source.new())
    target.renew.assert_called_once_with(source.updates())


def test_should_notify_observer(source: Source[Any]) -> None:
    target = MagicMock()
    observer = MagicMock()

    Sync(source=source, target=target, dry_run=True).attach(observer).run()

    observer.before_prune.assert_called_once_with(len(list(source.absent())))
    observer.after_prune.assert_called_once()

    observer.before_load.assert_called_once_with(len(list(source.new())))
    observer.after_load.assert_called_once()

    observer.before_update.assert_called_once_with(len(list(source.updates())))
    observer.after_update.assert_called_once()


def test_should_not_notify_observer(source: Source[Any]) -> None:
    target = MagicMock()
    observer = MagicMock()

    Sync(source=source, target=target, dry_run=True).attach(observer, when=False).run()

    observer.before_prune.assert_not_called()
    observer.after_prune.assert_not_called()

    observer.before_load.assert_not_called()
    observer.after_load.assert_not_called()

    observer.before_update.assert_not_called()
    observer.after_update.assert_not_called()


def test_should_log(source: Source[Any]) -> None:
    log = []

    def log_fn(message: str) -> None:
        log.append(message)

    Sync(source=source, target=MagicMock()).with_log(using=log_fn).run()

    assert log == [
        f"Total # of absent items: {len(list(source.absent()))}",
        "Pruning completed",
        f"Total # of new items: {len(list(source.new()))}",
        "Loading completed",
        f"Total # of updates: {len(list(source.updates()))}",
        "Updating completed",
    ]


@pytest.fixture
def source(faker: Faker) -> SourcePreSet[int | str]:
    return SourcePreSet(
        removals=faker.pyset(
            nb_elements=10,
            variable_nb_elements=True,
            value_types=[int, str],
        ),
        additions=faker.pyset(
            nb_elements=10,
            variable_nb_elements=True,
            value_types=[int, str],
        ),
        changes=faker.pyset(
            nb_elements=10,
            variable_nb_elements=True,
            value_types=[int, str],
        ),
    )
