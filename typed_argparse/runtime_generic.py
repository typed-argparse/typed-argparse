import inspect
import typing
from typing import Any

# Workaround for generic type erasure:
# https://github.com/python/typing/issues/629#issuecomment-829629259


class Proxy:
    def __init__(self, generic: Any) -> None:
        object.__setattr__(self, "_generic", generic)

    def __getattr__(self, name: str) -> Any:
        if typing._is_dunder(name):  # type: ignore # noqa
            return getattr(self._generic, name)
        origin = self._generic.__origin__
        obj = getattr(origin, name)
        if inspect.ismethod(obj) and isinstance(obj.__self__, type):
            return lambda *a, **kw: obj.__func__(self, *a, *kw)
        else:
            return obj

    def __setattr__(self, name: str, value: Any) -> Any:
        return setattr(self._generic, name, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._generic.__call__(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} of {self._generic!r}>"


class RuntimeGeneric:
    def __class_getitem__(cls, key: str) -> Any:
        generic = super().__class_getitem__(key)  # type: ignore
        if getattr(generic, "__origin__", None):
            return Proxy(generic)
        else:
            return generic
