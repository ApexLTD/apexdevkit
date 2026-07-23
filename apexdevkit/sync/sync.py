from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from typing import Any, Self

from .observer import DefaultLog, ObservableSync
from .source import Source
from .target import Target


@dataclass(frozen=True, kw_only=True)
class Sync(ObservableSync):
    source: Source
    target: Target

    dry_run: bool = False

    def with_log(self, using: Callable[[str], None]) -> Self:
        return self.attach(DefaultLog(echo=using))

    def run(self, prune: bool = True, load: bool = True, update: bool = True) -> None:
        if prune:
            self.prune()

        if load:
            self.load()

        if update:
            self.update()

    def prune(self) -> None:
        (
            SyncProbe(source=set(self.source.absent()))
            .disable(when=self.dry_run)
            .notify(using=self.before_prune)
            .send(using=self.target.prune)
            .notify(using=self.after_prune)
        )

    def load(self) -> None:
        (
            SyncProbe(source=set(self.source.new()))
            .disable(when=self.dry_run)
            .notify(using=self.before_load)
            .send(using=self.target.load)
            .notify(using=self.after_load)
        )

    def update(self) -> None:
        (
            SyncProbe(source=set(self.source.updates()))
            .disable(when=self.dry_run)
            .notify(using=self.before_update)
            .send(using=self.target.renew)
            .notify(using=self.after_update)
        )


@dataclass(frozen=True, kw_only=True)
class SyncProbe:
    source: Collection[Any]

    is_enabled: bool = True

    def disable(self, when: bool) -> SyncProbe:
        return SyncProbe(source=self.source, is_enabled=not when)

    def notify(self, using: Callable[[int], None]) -> SyncProbe:
        using(len(self.source))

        return self

    def send(self, using: Callable[[Iterable[Any]], None]) -> SyncProbe:
        if self.is_enabled and len(self.source) > 0:
            using(self.source)

        return self
