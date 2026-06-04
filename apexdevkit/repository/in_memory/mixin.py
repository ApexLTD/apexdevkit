from collections import defaultdict
from collections.abc import MutableMapping
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from .store import InMemoryByteStore, KeyValueStore


@dataclass(frozen=True)
class CacheMixin:
    @cached_property
    def _entries(self) -> MutableMapping[str, KeyValueStore[Any]]:
        return defaultdict(InMemoryByteStore)

    def store_for(self, name: str) -> KeyValueStore[Any]:
        return self._entries[name]

    def clear(self) -> None:
        self._entries.clear()
