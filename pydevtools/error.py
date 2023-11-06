from dataclasses import dataclass
from typing import Any


@dataclass
class ExistsError(Exception):
    id: Any


@dataclass
class DoesNotExistError(Exception):
    id: Any
