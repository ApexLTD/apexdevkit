from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T", contravariant=True)


class Target(Protocol[T]):  # pragma: no cover
    def prune(self, source: Iterable[T]) -> Any:
        pass

    def load(self, source: Iterable[T]) -> Any:
        pass

    def renew(self, source: Iterable[T]) -> Any:
        pass


class NoTarget(Generic[T]):  # pragma: no cover
    def prune(self, source: Iterable[T]) -> Any:
        pass

    def load(self, source: Iterable[T]) -> Any:
        pass

    def renew(self, source: Iterable[T]) -> Any:
        pass


@dataclass(frozen=True, kw_only=True)
class TargetDecorator(Generic[T]):
    inner: Target[T] = field(default_factory=NoTarget)

    def prune(self, source: Iterable[T]) -> Any:
        self.inner.prune(source)

    def load(self, source: Iterable[T]) -> Any:
        self.inner.load(source)

    def renew(self, source: Iterable[T]) -> Any:
        self.inner.renew(source)


class TargetFailing(Generic[T]):
    @staticmethod
    def on_everything(using: Target[T] | None = None) -> Target[T]:
        return TargetFailing.on_prune(
            using=TargetFailing.on_load(
                using=TargetFailing.on_update(
                    using=using or NoTarget(),
                ),
            ),
        )

    @staticmethod
    def on_prune(using: Target[T] | None = None) -> Target[T]:
        return _FailOnPrune(inner=using or NoTarget())

    @staticmethod
    def on_load(using: Target[T] | None = None) -> Target[T]:
        return _FailOnLoad(inner=using or NoTarget())

    @staticmethod
    def on_update(using: Target[T] | None = None) -> Target[T]:
        return _FailOnUpdate(inner=using or NoTarget())


@dataclass(frozen=True, kw_only=True)
class _FailOnPrune(TargetDecorator[T]):
    def prune(self, source: Iterable[T]) -> Any:  # pragma: no cover
        raise RuntimeError(source)


@dataclass(frozen=True, kw_only=True)
class _FailOnLoad(TargetDecorator[T]):
    def load(self, source: Iterable[T]) -> Any:  # pragma: no cover
        raise RuntimeError(source)


@dataclass(frozen=True, kw_only=True)
class _FailOnUpdate(TargetDecorator[T]):
    def renew(self, source: Iterable[T]) -> Any:  # pragma: no cover
        raise RuntimeError(source)
