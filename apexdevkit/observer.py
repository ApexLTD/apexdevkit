from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Self


@dataclass(frozen=True, kw_only=True)
class Publisher[T]:
    observers: list[_Subscriber[T]] = field(default_factory=list)

    def attach(self, observer: _Subscriber[T]) -> Self:
        self.observers.append(observer)

        return self

    def notify_create_one(self, item: T) -> T:
        self.notify_create(items=[item])

        return item

    def notify_create(self, *, items: list[T]) -> None:
        for observer in self.observers:
            observer.on_create(items=items)

    def notify_update_one(self, item: T) -> T:
        self.notify_update(items=[item])

        return item

    def notify_update(self, *, items: list[T]) -> None:
        for observer in self.observers:
            observer.on_update(items=items)

    def notify_delete_one(self, item: T) -> T:
        self.notify_delete(items=[item])

        return item

    def notify_delete(self, *, items: list[T]) -> None:
        for observer in self.observers:
            observer.on_delete(items=items)


class _Subscriber[T](Protocol):  # pragma: no cover
    def on_create(self, *, items: list[T]) -> None:
        pass

    def on_update(self, *, items: list[T]) -> None:
        pass

    def on_delete(self, *, items: list[T]) -> None:
        pass


class Subscriber[T]:  # pragma: no cover
    def on_create(self, *, items: list[T]) -> None:
        pass

    def on_update(self, *, items: list[T]) -> None:
        pass

    def on_delete(self, *, items: list[T]) -> None:
        pass
