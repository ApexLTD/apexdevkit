import inspect
from typing import Any, Callable, TypeVar, cast
from warnings import warn

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(warning: str) -> Callable[[F], F]:
    """Marks a function, method, or class as deprecated.

    Do not use this annotation inside dataclass annotation.
    Use it in this order instead:

    @deprecated("Replace this class with NewClass")
    @dataclass\n
    class OldClass:

    Do not use this annotation around generic classes. For
    example:

    class GenericClass(Generic[T])"""

    def decorator(obj: F) -> F:
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            return cast(F, _wrap_function(obj, warning))
        elif inspect.isclass(obj):
            return cast(F, _deprecate_class(obj, warning))
        else:
            raise TypeError(
                f"Unsupported type for deprecation: {type(obj)}"
            )  # pragma: no cover

    return decorator


def _wrap_function(func: F, warning: str) -> F:
    def wrapper(*args: Any, **kwargs: dict[str, Any]) -> Any:
        warn(warning, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return cast(F, wrapper)


def _deprecate_class(cls: type, warning: str) -> type:
    class DeprecatedClass(cls):  # type: ignore
        def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
            warn(warning, category=DeprecationWarning, stacklevel=2)
            super().__init__(*args, **kwargs)

    return cast(type, DeprecatedClass)
