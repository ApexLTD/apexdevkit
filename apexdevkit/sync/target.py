from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

T = TypeVar("T")


class Target(Protocol):  # pragma: no cover
    def prune(self, source: Iterable[T]) -> None:
        pass

    def load(self, source: Iterable[T]) -> None:
        pass

    def renew(self, source: Iterable[T]) -> None:
        pass


class NoTarget:  # pragma: no cover
    def prune(self, source: Iterable[T]) -> None:
        pass

    def load(self, source: Iterable[T]) -> None:
        pass

    def renew(self, source: Iterable[T]) -> None:
        pass


@dataclass(frozen=True, kw_only=True)
class TargetDecorator:
    inner: Target = field(default_factory=NoTarget)

    def prune(self, source: Iterable[T]) -> None:
        self.inner.prune(source)

    def load(self, source: Iterable[T]) -> None:
        self.inner.load(source)

    def renew(self, source: Iterable[T]) -> None:
        self.inner.renew(source)


class TargetFailing:
    @staticmethod
    def on_everything(using: Target | None = None) -> Target:
        return TargetFailing.on_prune(
            using=TargetFailing.on_load(
                using=TargetFailing.on_update(
                    using=using or NoTarget(),
                ),
            ),
        )

    @staticmethod
    def on_prune(using: Target | None = None) -> Target:
        return TargetFailing.OnPrune(inner=using or NoTarget())

    @dataclass(frozen=True, kw_only=True)
    class OnPrune(TargetDecorator):
        def prune(self, source: Iterable[T]) -> None:  # pragma: no cover
            raise RuntimeError(source)

    @staticmethod
    def on_load(using: Target | None = None) -> Target:
        return TargetFailing.OnLoad(inner=using or NoTarget())

    @dataclass(frozen=True, kw_only=True)
    class OnLoad(TargetDecorator):
        def load(self, source: Iterable[T]) -> None:  # pragma: no cover
            raise RuntimeError(source)

    @staticmethod
    def on_update(using: Target | None = None) -> Target:
        return TargetFailing.OnUpdate(inner=using or NoTarget())

    @dataclass(frozen=True, kw_only=True)
    class OnUpdate(TargetDecorator):
        def renew(self, source: Iterable[T]) -> None:  # pragma: no cover
            raise RuntimeError(source)
