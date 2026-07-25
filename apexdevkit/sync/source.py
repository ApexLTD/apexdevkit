from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from apexdevkit.key_fn import AttributeKey, KeyFn

T = TypeVar("T")


class Source(Protocol):  # pragma: no cover
    def absent(self) -> Iterable[T]:
        pass

    def new(self) -> Iterable[T]:
        pass

    def updates(self) -> Iterable[T]:
        pass


@dataclass(frozen=True)
class EmptySource:  # pragma: no cover
    def absent(self) -> Iterable[T]:
        return []

    def new(self) -> Iterable[T]:
        return []

    def updates(self) -> Iterable[T]:
        return []


@dataclass(frozen=True, kw_only=True)
class SourceDecorator:  # pragma: no cover
    inner: Source = field(default_factory=EmptySource)

    def absent(self) -> Iterable[T]:
        return self.inner.absent()

    def new(self) -> Iterable[T]:
        return self.inner.new()

    def updates(self) -> Iterable[T]:
        return self.inner.updates()


@dataclass(frozen=True, kw_only=True)
class SourcePreSet(Generic[T]):
    removals: Iterable[T]
    additions: Iterable[T]
    changes: Iterable[T]

    def absent(self) -> Iterable[T]:
        return self.removals

    def new(self) -> Iterable[T]:
        return self.additions

    def updates(self) -> Iterable[T]:
        return self.changes


class SourceFailing:
    @staticmethod
    def on_everything(using: Source | None = None) -> Source:
        return SourceFailing.on_absent(
            using=SourceFailing.on_new(
                using=SourceFailing.on_update(
                    using=using or EmptySource(),
                ),
            ),
        )

    @staticmethod
    def on_absent(using: Source | None = None) -> Source:
        return SourceFailing.OnAbsent(inner=using or EmptySource())

    @dataclass(frozen=True, kw_only=True)
    class OnAbsent(SourceDecorator):
        def absent(self) -> Iterable[T]:  # pragma: no cover
            raise RuntimeError("Should not request absent!")

    @staticmethod
    def on_new(using: Source | None = None) -> Source:
        return SourceFailing.OnNew(inner=using or EmptySource())

    @dataclass(frozen=True, kw_only=True)
    class OnNew(SourceDecorator):
        def new(self) -> Iterable[T]:  # pragma: no cover
            raise RuntimeError("Should not request new!")

    @staticmethod
    def on_update(using: Source | None = None) -> Source:
        return SourceFailing.OnUpdate(inner=using or EmptySource())

    @dataclass(frozen=True, kw_only=True)
    class OnUpdate(SourceDecorator):
        def updates(self) -> Iterable[T]:  # pragma: no cover
            raise RuntimeError("Should not request updates!")


@dataclass(frozen=True, kw_only=True)
class SourceDiscriminator(Generic[T]):
    current: Iterable[T]
    latest: Iterable[T]

    key_fn: KeyFn = AttributeKey("id")

    def absent(self) -> Iterable[T]:
        index = {self.key_fn(item) for item in self.latest}

        return [item for item in self.current if self.key_fn(item) not in index]

    def new(self) -> Iterable[T]:
        index = {self.key_fn(item) for item in self.current}

        return [item for item in self.latest if self.key_fn(item) not in index]

    def updates(self) -> Iterable[T]:
        return set(self.latest).difference(self.current)
