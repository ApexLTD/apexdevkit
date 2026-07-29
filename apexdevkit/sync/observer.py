from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, Self


@dataclass(frozen=True)
class ObservableSync:
    observers: list[SyncObserver] = field(default_factory=list)

    def attach(self, observer: SyncObserver, when: bool = True) -> Self:
        if when:
            self.observers.append(observer)

        return self

    def before_prune(self, n_items: int) -> None:
        for observer in self.observers:
            observer.before_prune(n_items)

    def after_prune(self, n_items: int) -> None:
        _ = n_items

        for observer in self.observers:
            observer.after_prune()

    def before_load(self, n_items: int) -> None:
        for observer in self.observers:
            observer.before_load(n_items)

    def after_load(self, n_items: int) -> None:
        _ = n_items

        for observer in self.observers:
            observer.after_load()

    def before_update(self, n_items: int) -> None:
        for observer in self.observers:
            observer.before_update(n_items)

    def after_update(self, n_items: int) -> None:
        _ = n_items

        for observer in self.observers:
            observer.after_update()


class SyncObserver(Protocol):  # pragma: no cover
    def before_prune(self, n_items: int) -> None:
        pass

    def after_prune(self) -> None:
        pass

    def before_load(self, n_items: int) -> None:
        pass

    def after_load(self) -> None:
        pass

    def before_update(self, n_items: int) -> None:
        pass

    def after_update(self) -> None:
        pass


@dataclass(frozen=True)
class DefaultLog:
    name: str = "items"
    echo: Callable[[str], None] = print

    def before_prune(self, n_items: int) -> None:
        self.echo(f"Total # of absent {self.name}: {n_items}")

    def after_prune(self) -> None:
        self.echo("Pruning completed")

    def before_load(self, n_items: int) -> None:
        self.echo(f"Total # of new {self.name}: {n_items}")

    def after_load(self) -> None:
        self.echo("Loading completed")

    def before_update(self, n_items: int) -> None:
        self.echo(f"Total # of changed {self.name}: {n_items}")

    def after_update(self) -> None:
        self.echo("Updating completed")
