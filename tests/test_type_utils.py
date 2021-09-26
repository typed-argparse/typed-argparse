from typing import List, Optional
from typing_extensions import Literal

from typed_argparse.type_utils import TypeAnnotation


# -----------------------------------------------------------------------------
# TypeAnnotation
# -----------------------------------------------------------------------------


def test_type_annotation__scalar_types() -> None:
    t = TypeAnnotation(str)
    assert t.origin is None
    assert t.args == ()
    assert t.get_underlying_if_optional() is None
    assert t.get_underlying_if_list() is None

    assert t.validate("foo") == ("foo", None)
    assert t.validate(12345) == (12345, "value is of type 'int', expected 'str'")


def test_type_annotation__user_class() -> None:
    class MyClass:
        def __init__(self) -> None:
            self.a: int = 42
            self.b: str = "foo"

    t = TypeAnnotation(MyClass)
    assert t.origin is None
    assert t.args == ()
    assert t.get_underlying_if_optional() is None
    assert t.get_underlying_if_list() is None

    my_class = MyClass()
    assert t.validate(my_class) == (my_class, None)
    assert t.validate("foo") == ("foo", "value is of type 'str', expected 'MyClass'")
    assert t.validate(12345) == (12345, "value is of type 'int', expected 'MyClass'")


def test_type_annotation__optional() -> None:
    t = TypeAnnotation(Optional[str])
    t_underlying = t.get_underlying_if_optional()
    assert t_underlying is not None
    assert t_underlying.raw_type is str

    assert t.validate("foo") == ("foo", None)
    assert t.validate(None) == (None, None)


def test_type_annotation__list() -> None:
    t = TypeAnnotation(List[str])
    t_underlying = t.get_underlying_if_list()
    assert t_underlying is not None
    assert t_underlying.raw_type is str

    assert t.validate(["a", "b", "c"]) == (["a", "b", "c"], None)
    assert t.validate("foo") == ("foo", "value is of type 'str', expected 'list'")


def test_type_annotation__mixed_list_optional() -> None:
    t = TypeAnnotation(Optional[List[str]]).get_underlying_if_optional()
    assert t is not None
    t = t.get_underlying_if_list()
    assert t is not None
    assert t.raw_type is str

    t = TypeAnnotation(List[Optional[str]]).get_underlying_if_list()
    assert t is not None
    t = t.get_underlying_if_optional()
    assert t is not None
    assert t.raw_type is str


def test_type_annotation__literals() -> None:
    t = TypeAnnotation(Literal[1, 2, 3])
    assert t.validate(1) == (1, None)
    assert t.validate(2) == (2, None)
    assert t.validate(3) == (3, None)
    assert t.validate(4) == (4, "value 4 does not match any allowed literal value in (1, 2, 3)")
