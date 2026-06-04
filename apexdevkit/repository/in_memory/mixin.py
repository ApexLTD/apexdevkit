from dataclasses import dataclass, field
from typing import Any

from .store import InMemoryByteStore, KeyValueStore


@dataclass(frozen=True)
class CacheMixin:
    cache: InMemoryByteStore.Cache = field(default_factory=InMemoryByteStore.Cache)

    def store_for(self, resource: str) -> KeyValueStore[Any]:
        return self.cache.store_for(resource)
