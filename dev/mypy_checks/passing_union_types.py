# Inspired by:
# https://github.com/python/mypy/issues/9773#issuecomment-736808369
#
# Works under 3.6, but not under newer Python versions because of:
# https://github.com/python/typing/issues/629
#
# Possible work-around in comment:
# https://github.com/python/typing/issues/629#issuecomment-829629259

from typing import TypeVar, Generic, Union


T = TypeVar("T")


class WithUnionType(Generic[T]):
    @classmethod
    def validate(cls, value: object) -> T:
        args = cls.__args__  # type: ignore
        print(f"type args: {args!r}")
        return None  # type: ignore


MyUnion = Union[int, str]


def f(x: MyUnion) -> None:
    print(x)


def main() -> None:
    x = WithUnionType[MyUnion].validate(None)
    f(x)


main()
