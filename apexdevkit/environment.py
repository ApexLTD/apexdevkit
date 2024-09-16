import os
from dataclasses import field


def environment_variable(name: str, *, default: str | None = None) -> str:
    return field(default_factory=lambda: value_of_env(variable=name, default=default))


def value_of_env(*, variable: str, default: str | None = None) -> str:
    return os.environ[variable] if default is None else os.getenv(variable, default)
