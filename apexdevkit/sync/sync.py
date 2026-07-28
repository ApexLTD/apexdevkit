from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field, replace
from typing import Any, Generic, Self, TypeVar

from apexdevkit.key_fn import KeyFn

from .observer import DefaultLog, ObservableSync
from .source import EmptySource, Source, SourceDiscriminator, SourcePreSet
from .target import IterableTarget, NoTarget, Target

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class Sync(ObservableSync, Generic[T]):
    source: Source[T] = field(default_factory=EmptySource)
    target: Target[T] = field(default_factory=NoTarget)

    dry_run: bool = False

    def purge(self) -> _Purge[T]:
        return _Purge[T](sync=self)

    def with_discriminated(
        self,
        target: IterableTarget[T],
        source: Iterable[T],
        using: KeyFn | None = None,
    ) -> Sync[T]:
        return self.with_target(target).and_source(
            SourceDiscriminator(
                current=list(target),
                latest=source,
                key_fn=using,
            )
        )

    def and_target(self, value: Target[T]) -> Sync[T]:
        return self.with_target(value)

    def with_target(self, value: Target[T]) -> Sync[T]:
        return replace(self, target=value)

    def and_source(self, value: Source[T]) -> Sync[T]:
        return self.with_source(value)

    def with_source(self, value: Source[T]) -> Sync[T]:
        return replace(self, source=value)

    def with_log(self, using: Callable[[str], None]) -> Self:
        return self.attach(DefaultLog(echo=using))

    def dry(self, *, when: bool = True) -> Sync[T]:
        return replace(self, dry_run=when)

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
class _Purge(Generic[T]):
    sync: Sync[T]

    def target(self, value: IterableTarget[T]) -> _Purge[T]:
        return _Purge[T](
            sync=replace(
                self.sync,
                target=value,
                source=SourcePreSet[T](removals=list(value)),
            )
        )

    def __call__(self) -> None:
        self.run()

    def run(self) -> None:
        self.sync.prune()


@dataclass(frozen=True, kw_only=True)
class SyncProbe:
    source: Collection[Any]

    is_enabled: bool = True

    def disable(self, when: bool) -> SyncProbe:
        return SyncProbe(source=self.source, is_enabled=not when)

    def notify(self, using: Callable[[int], None]) -> SyncProbe:
        using(len(self.source))

        return self

    def send(self, using: Callable[[Iterable[Any]], Iterable[Any] | None]) -> SyncProbe:
        result = None
        if self.is_enabled and len(self.source) > 0:
            result = using(self.source)

        if result:
            list(result)

        return self
