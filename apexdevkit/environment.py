
from pypebbles.runtime import Environment


def environment_variable(name: str, *, default: str | None = None) -> str:
    return Environment().inject(variable=name, default=default)


def value_of_env(*, variable: str, default: str | None = None) -> str:
    return Environment().value_of(variable=variable, default=default)
