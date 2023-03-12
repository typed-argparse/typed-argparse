import argparse
import enum
from typing import List, NewType, Optional, Union

import pytest
from typing_extensions import Literal

from typed_argparse import TypedArgs, WithUnionType

# -----------------------------------------------------------------------------
# Basics
# -----------------------------------------------------------------------------


def test_basic_1() -> None:
    class Args(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


def test_basic_2() -> None:
    class Args(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num=42)
    args = Args.from_argparse(args_namespace)
    assert args.num == 42


def test_missing_field__single() -> None:
    class Args(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace()
    with pytest.raises(
        TypeError,
        match="Arguments object is missing argument 'foo'",
    ):
        Args.from_argparse(args_namespace)


def test_missing_field__multiple() -> None:
    class Args(TypedArgs):
        foo: str
        bar: str

    args_namespace = argparse.Namespace()
    with pytest.raises(
        TypeError,
        match=r"Arguments object is missing arguments \['foo', 'bar'\]",
    ):
        Args.from_argparse(args_namespace)


def test_extra_field__single() -> None:
    class Args(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar")
    with pytest.raises(
        TypeError,
        match="Arguments object has an unexpected extra argument 'bar'",
    ):
        Args.from_argparse(args_namespace, disallow_extra_args=True)


def test_extra_field__multiple() -> None:
    class Args(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar", baz="baz")
    with pytest.raises(
        TypeError,
        match=r"Arguments object has unexpected extra arguments \['bar', 'baz'\]",
    ):
        Args.from_argparse(args_namespace, disallow_extra_args=True)


def test_simple_type_mismatch_1() -> None:
    class Args(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'foo': value is of type 'int', expected 'str'",
    ):
        Args.from_argparse(args_namespace)


def test_simple_type_mismatch_2() -> None:
    class Args(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num="foo")
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'num': value is of type 'str', expected 'int'",
    ):
        Args.from_argparse(args_namespace)


def test_annotation_that_isnt_a_type() -> None:
    # In principle this should already be prevented by mypy itself (that's why we
    # need to type-ignore the mistake here), but let's make sure that it still
    # would produce a comprehensible runtime error.
    class Args(TypedArgs):
        num: 42  # type: ignore

    args_namespace = argparse.Namespace(num=42)
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'num': "
        "Type annotation is of type 'int', expected 'type'",
    ):
        Args.from_argparse(args_namespace)


# -----------------------------------------------------------------------------
# Lists
# -----------------------------------------------------------------------------


def test_lists_1() -> None:
    class Args(TypedArgs):
        foo: List[str]

    args_namespace = argparse.Namespace(foo=["a", "b", "c"])
    args = Args.from_argparse(args_namespace)
    assert args.foo == ["a", "b", "c"]


def test_lists_2() -> None:
    class Args(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=[1, 2, 3])
    args = Args.from_argparse(args_namespace)
    assert args.num == [1, 2, 3]


def test_lists__should_coerce_empty_lists_automatically() -> None:
    class Args(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=None)
    args = Args.from_argparse(args_namespace)
    assert args.num == []


def test_lists__should_not_coerce_empty_lists_automatically_if_optional() -> None:
    class Args(TypedArgs):
        num: Optional[List[int]]

    args_namespace = argparse.Namespace(num=None)
    args = Args.from_argparse(args_namespace)
    assert args.num is None


def test_lists__elements_type_mismatch_1() -> None:
    class Args(TypedArgs):
        foo: List[str]

    args_namespace = argparse.Namespace(foo=["a", 2, "c"])
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'foo': not all elements "
        r"of the list have proper type \(value is of type 'int', expected 'str'\)",
    ):
        Args.from_argparse(args_namespace)


def test_lists__elements_type_mismatch_2() -> None:
    class Args(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=["a", 2, "c"])
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'num': not all elements "
        r"of the list have proper type \(value is of type 'str', expected 'int'\)",
    ):
        Args.from_argparse(args_namespace)


# -----------------------------------------------------------------------------
# Optionals
# -----------------------------------------------------------------------------


def test_optional_1() -> None:
    class Args(TypedArgs):
        foo: Optional[str]

    args_namespace = argparse.Namespace(foo=None)
    args = Args.from_argparse(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


def test_optional_2() -> None:
    class Args(TypedArgs):
        num: Optional[int]

    args_namespace = argparse.Namespace(num=None)
    args = Args.from_argparse(args_namespace)
    assert args.num is None

    args_namespace = argparse.Namespace(num=42)
    args = Args.from_argparse(args_namespace)
    assert args.num == 42


def test_optional__type_mismatch() -> None:
    class Args(TypedArgs):
        foo: Optional[str]

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError, match="Failed to validate argument 'foo': value is of type 'int', expected 'str'"
    ):
        Args.from_argparse(args_namespace)


def test_optional__as_union_type_1() -> None:
    class Args(TypedArgs):
        foo: Union[str, None]

    args_namespace = argparse.Namespace(foo=None)
    args = Args.from_argparse(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


def test_optional__as_union_type_2() -> None:
    class Args(TypedArgs):
        foo: Union[None, str]

    args_namespace = argparse.Namespace(foo=None)
    args = Args.from_argparse(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


# -----------------------------------------------------------------------------
# Literal
# -----------------------------------------------------------------------------


def test_literal() -> None:
    class Args(TypedArgs):
        foo: Literal[1, 2, 3]

    args_namespace = argparse.Namespace(foo=1)
    args = Args.from_argparse(args_namespace)
    assert args.foo == 1

    args_namespace = argparse.Namespace(foo=4)
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'foo': "
        r"value 4 does not match any allowed literal value in \(1, 2, 3\)",
    ):
        Args.from_argparse(args_namespace)


# -----------------------------------------------------------------------------
# Enum
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__parse_from_str(use_literal_enum: bool) -> None:
    if use_literal_enum:

        class StrEnum(str, enum.Enum):
            a = "a"
            b = "b"
            c = "c"

    else:

        class StrEnum(enum.Enum):  # type: ignore
            a = "a"
            b = "b"
            c = "c"

    class Args(TypedArgs):
        foo: StrEnum

    args_namespace = argparse.Namespace(foo="a")
    args = Args.from_argparse(args_namespace)
    assert args.foo is StrEnum.a
    if use_literal_enum:
        assert isinstance(args.foo, str)
        assert args.foo == "a"

    args_namespace = argparse.Namespace(foo="d")
    with pytest.raises(TypeError) as e:
        Args.from_argparse(args_namespace)
    assert (
        "Failed to validate argument 'foo': value d does not match any allowed enum value "
        "in (<StrEnum.a: 'a'>, <StrEnum.b: 'b'>, <StrEnum.c: 'c'>)"
    ) == str(e.value)


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__parse_from_int(use_literal_enum: bool) -> None:
    if use_literal_enum:

        class IntEnum(int, enum.Enum):
            a = 1
            b = 2
            c = 3

    else:

        class IntEnum(enum.Enum):  # type: ignore
            a = 1
            b = 2
            c = 3

    class Args(TypedArgs):
        foo: IntEnum

    args_namespace = argparse.Namespace(foo=1)
    args = Args.from_argparse(args_namespace)
    assert args.foo is IntEnum.a
    if use_literal_enum:
        assert isinstance(args.foo, int)
        assert args.foo == 1  # type: ignore

    args_namespace = argparse.Namespace(foo=4)
    with pytest.raises(TypeError) as e:
        Args.from_argparse(args_namespace)
    assert (
        "Failed to validate argument 'foo': value 4 does not match any allowed enum value "
        "in (<IntEnum.a: 1>, <IntEnum.b: 2>, <IntEnum.c: 3>)"
    ) == str(e.value)


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__use_with_choice(use_literal_enum: bool) -> None:
    if use_literal_enum:

        class StrEnum(str, enum.Enum):
            a = "a"
            b = "b"
            c = "c"

    else:

        class StrEnum(enum.Enum):  # type: ignore
            a = "a"
            b = "b"
            c = "c"

    class Args(TypedArgs):
        foo: StrEnum

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--foo",
        type=StrEnum,
        choices=list(StrEnum),
    )

    args = Args.from_argparse(parser.parse_args(["--foo", "a"]))
    assert args.foo is StrEnum.a


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__use_with_choice__with_default(use_literal_enum: bool) -> None:
    if use_literal_enum:

        class StrEnum(str, enum.Enum):
            a = "a"
            b = "b"
            c = "c"

    else:

        class StrEnum(enum.Enum):  # type: ignore
            a = "a"
            b = "b"
            c = "c"

    class Args(TypedArgs):
        foo: StrEnum

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--foo",
        type=StrEnum,
        choices=list(StrEnum),
        default=StrEnum.a,
    )

    args = Args.from_argparse(parser.parse_args([]))
    assert args.foo is StrEnum.a


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__use_with_choice__with_get_choices_from(use_literal_enum: bool) -> None:
    if use_literal_enum:

        class StrEnum(str, enum.Enum):
            a = "a"
            b = "b"
            c = "c"

    else:

        class StrEnum(enum.Enum):  # type: ignore
            a = "a"
            b = "b"
            c = "c"

    class Args(TypedArgs):
        foo: StrEnum

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--foo",
        type=StrEnum,
        choices=Args.get_choices_from("foo"),
    )

    args = Args.from_argparse(parser.parse_args(["--foo", "a"]))
    assert args.foo is StrEnum.a


# -----------------------------------------------------------------------------
# NewType
# -----------------------------------------------------------------------------


def test_new_type() -> None:
    MyString = NewType("MyString", str)

    class Args(TypedArgs):
        foo: MyString

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--foo",
        type=MyString,
    )

    args = Args.from_argparse(parser.parse_args(["--foo", "value"]))
    assert args.foo == MyString("value")


# -----------------------------------------------------------------------------
# Union
# -----------------------------------------------------------------------------


def test_union() -> None:
    class Args(TypedArgs):
        foo: Union[str, int]

    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=lambda x: str(x))
    args = Args.from_argparse(parser.parse_args(["--foo", "42"]))
    assert args.foo == "42"

    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=lambda x: int(x))
    args = Args.from_argparse(parser.parse_args(["--foo", "42"]))
    assert args.foo == 42

    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=lambda x: float(x))
    with pytest.raises(TypeError) as e:
        Args.from_argparse(parser.parse_args(["--foo", "42"]))
    assert (
        "Failed to validate argument 'foo': value 42.0 did not match any type of union:\n"
        " - value is of type 'float', expected 'str'\n"
        " - value is of type 'float', expected 'int'"
    ) == str(e.value)


# -----------------------------------------------------------------------------
# WithUnionType
# -----------------------------------------------------------------------------


def test_with_union_type() -> None:
    class Foo(TypedArgs):
        mode: Literal["foo"]

    class Bar(TypedArgs):
        mode: Literal["bar"]

    Args = Union[Foo, Bar]

    args_namespace = argparse.Namespace(mode="foo")
    args = WithUnionType[Args].validate(args_namespace)
    assert isinstance(args, Foo)

    args_namespace = argparse.Namespace(mode="bar")
    args = WithUnionType[Args].validate(args_namespace)
    assert isinstance(args, Bar)

    # No type of Union matching
    args_namespace = argparse.Namespace(mode="illegal")
    with pytest.raises(TypeError) as e:
        WithUnionType[Args].validate(args_namespace)
    expected = (
        "Validation failed against all sub types of union type:\n"
        " - Failed to validate argument 'mode': "
        "value illegal does not match any allowed literal value in ('foo',)\n"
        " - Failed to validate argument 'mode': "
        "value illegal does not match any allowed literal value in ('bar',)"
    )
    print(repr(str(e.value)))
    print(repr(expected))
    assert str(e.value) == expected

    # Illegal Union
    args_namespace = argparse.Namespace()
    with pytest.raises(TypeError) as e:
        WithUnionType[Union[str, int]].validate(args_namespace)
    expected = f"Type union {Union[str, int]} did not contain any sub types of type TypedArgs."
    print(repr(str(e.value)))
    print(repr(expected))
    assert str(e.value) == expected


# -----------------------------------------------------------------------------
# Mutually exclusive group
# -----------------------------------------------------------------------------


def test_mutually_exclusive_group() -> None:
    class Foo(TypedArgs):
        foo: str

    class Bar(TypedArgs):
        bar: str

    Args = Union[Foo, Bar]

    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--foo")
    g.add_argument("--bar")

    args = WithUnionType[Args].validate(parser.parse_args(["--foo", "foo"]))
    assert isinstance(args, Foo)
    assert args.foo == "foo"

    args = WithUnionType[Args].validate(parser.parse_args(["--bar", "bar"]))
    assert isinstance(args, Bar)
    assert args.bar == "bar"


# -----------------------------------------------------------------------------
# dunder methods
# -----------------------------------------------------------------------------


def test_string_representation() -> None:
    class Args(TypedArgs):
        a: str
        b: Optional[int]
        c: Optional[int]
        list: List[str]

    def parse_args(args: List[str]) -> Args:
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=str, required=True)
        parser.add_argument("--b", type=int)
        parser.add_argument("--c", type=int)
        parser.add_argument("--list", type=str, nargs="*")
        return Args.from_argparse(parser.parse_args(args))

    args = parse_args(["--a", "a", "--c", "42"])
    expected = "Args(a='a', b=None, c=42, list=[])"
    assert str(args) == expected
    assert repr(args) == expected


def test_eq_and_ne() -> None:
    class Args(TypedArgs):
        a: str
        b: int

    assert Args(a="foo", b=42) == Args(a="foo", b=42)
    assert Args(a="foo", b=42) != Args(a="foo", b=43)


# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------


def test_get_raw_args__check_for_name_collision_1() -> None:
    class Args(TypedArgs):
        from_argparse: str  # type: ignore   # error on purpose for testing

    args_namespace = argparse.Namespace(from_argparse="foo")
    with pytest.raises(
        TypeError,
        match="A type must not have an argument called 'from_argparse'",
    ):
        Args.from_argparse(args_namespace)  # type: ignore


def test_get_raw_args__check_for_name_collision_2() -> None:
    class Args(TypedArgs):
        get_choices_from: str  # type: ignore   # error on purpose for testing

    args_namespace = argparse.Namespace(get_choices_from="foo")
    with pytest.raises(
        TypeError,
        match="A type must not have an argument called 'get_choices_from'",
    ):
        Args.from_argparse(args_namespace)


def test_check_reserved_names() -> None:
    fields_class = set(TypedArgs.__dict__)
    assert fields_class == {
        "__dataclass_transform__",
        "__dict__",
        "__doc__",
        "__eq__",
        "__hash__",
        "__init__",
        "__module__",
        "__ne__",
        "__repr__",
        "__str__",
        "__weakref__",
        "from_argparse",
        "get_choices_from",
    }


def test_temporary_backwards_compatibility() -> None:
    class Args(TypedArgs):
        foo: str

    argparse_namespace = argparse.Namespace(foo="foo")
    args = Args(argparse_namespace)
    assert args.foo == "foo"
