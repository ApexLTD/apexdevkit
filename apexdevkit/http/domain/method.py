from __future__ import annotations

from enum import Enum, auto


class HttpMethod(Enum):
    post = auto()
    get = auto()
    patch = auto()
    delete = auto()
    put = auto()
