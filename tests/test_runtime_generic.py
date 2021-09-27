from typed_argparse.runtime_generic import RuntimeGeneric


from typing import Any, List, TypeVar, Generic, Union


def test_runtime_generic() -> None:
    T = TypeVar("T")

    class WithUnionType(RuntimeGeneric, Generic[T]):
        @classmethod
        def get_generics(cls, box: List[Any]) -> None:
            args = getattr(cls, "__args__", None)
            if args is not None:
                box.append(args)
            return None

    MyUnion = Union[int, str]
    box: List[Any] = []
    WithUnionType[MyUnion].get_generics(box)

    assert len(box) > 0
    assert box[0][0] == MyUnion
