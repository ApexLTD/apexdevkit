from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

from apexdevkit.key_fn import AttributeKey, KeyFn

T = TypeVar("T", covariant=True)


class Source(Protocol[T]):  # pragma: no cover
    def absent(self) -> Iterable[T]:
        pass

    def new(self) -> Iterable[T]:
        pass

    def updates(self) -> Iterable[T]:
        pass


@dataclass(frozen=True)
class EmptySource(Generic[T]):  # pragma: no cover
    def absent(self) -> Iterable[T]:
        return []

    def new(self) -> Iterable[T]:
        return []

    def updates(self) -> Iterable[T]:
        return []


@dataclass(frozen=True, kw_only=True)
class SourceDecorator(Generic[T]):  # pragma: no cover
    inner: Source[T] = field(default_factory=EmptySource)

    def absent(self) -> Iterable[T]:
        return self.inner.absent()

    def new(self) -> Iterable[T]:
        return self.inner.new()

    def updates(self) -> Iterable[T]:
        return self.inner.updates()


@dataclass(frozen=True, kw_only=True)
class SourcePreSet(Generic[T]):
    removals: Iterable[T] = field(default_factory=list)
    additions: Iterable[T] = field(default_factory=list)
    changes: Iterable[T] = field(default_factory=list)

    def absent(self) -> Iterable[T]:
        return self.removals

    def new(self) -> Iterable[T]:
        return self.additions

    def updates(self) -> Iterable[T]:
        return self.changes


class SourceFailing(Generic[T]):
    @staticmethod
    def on_everything(using: Source[T] | None = None) -> Source[T]:
        return SourceFailing.on_absent(
            using=SourceFailing.on_new(
                using=SourceFailing.on_update(
                    using=using or EmptySource(),
                ),
            ),
        )

    @staticmethod
    def on_absent(using: Source[T] | None = None) -> Source[T]:
        return _FailOnAbsent(inner=using or EmptySource())

    @staticmethod
    def on_new(using: Source[T] | None = None) -> Source[T]:
        return _FailOnNew(inner=using or EmptySource())

    @staticmethod
    def on_update(using: Source[T] | None = None) -> Source[T]:
        return _FailOnUpdate(inner=using or EmptySource())


@dataclass(frozen=True, kw_only=True)
class _FailOnAbsent(SourceDecorator[T]):
    def absent(self) -> Iterable[T]:  # pragma: no cover
        raise RuntimeError("Should not request absent!")


@dataclass(frozen=True, kw_only=True)
class _FailOnNew(SourceDecorator[T]):
    def new(self) -> Iterable[T]:  # pragma: no cover
        raise RuntimeError("Should not request new!")


@dataclass(frozen=True, kw_only=True)
class _FailOnUpdate(SourceDecorator[T]):
    def updates(self) -> Iterable[T]:  # pragma: no cover
        raise RuntimeError("Should not request updates!")


@dataclass(frozen=True, kw_only=True)
class SourceDiscriminator(Generic[T]):
    current: Iterable[T]
    latest: Iterable[T]

    key_fn: KeyFn | None = None

    def absent(self) -> Iterable[T]:
        index = {self.key_of(item) for item in self.latest}

        return [item for item in self.current if self.key_of(item) not in index]

    def new(self) -> Iterable[T]:
        index = {self.key_of(item) for item in self.current}

        return [item for item in self.latest if self.key_of(item) not in index]

    def updates(self) -> Iterable[T]:
        index = {self.key_of(item) for item in self.current}

        return [
            item
            for item in set(self.latest).difference(self.current)
            if self.key_of(item) in index
        ]

    def key_of(self, item: Any) -> str:
        key_fn = self.key_fn or AttributeKey("id")

        return key_fn(item)
