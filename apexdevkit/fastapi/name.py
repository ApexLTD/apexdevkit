from __future__ import annotations

from dataclasses import dataclass

from apexdevkit.http import HttpUrl


@dataclass
class RestfulName:
    singular: str

    plural: str = ""

    def __post_init__(self) -> None:
        self.plural = self.plural or as_plural(self.singular)

    def __add__(self, other: str) -> str:
        return HttpUrl(self.plural) + other


def as_plural(singular: str) -> str:
    suffixes = {
        "y": "ies",
        "ch": "ches",
        "sh": "shes",
        "s": "ses",
        "z": "zes",
        "x": "xes",
        "fe": "ves",
        "f": "ves",
    }

    for singular_suffix, plural_suffix in suffixes.items():
        if singular.endswith(singular_suffix):
            return singular.removesuffix(singular_suffix) + plural_suffix

    return singular + "s"
