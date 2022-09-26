import typing

T = typing.TypeVar("T")

if hasattr(typing, "dataclass_transform"):
    dataclass_transform = typing.dataclass_transform  # type: ignore
else:

    def dataclass_transform(
        *,
        eq_default: bool = True,
        order_default: bool = False,
        kw_only_default: bool = False,
        field_specifiers: typing.Tuple[
            typing.Union[typing.Type[typing.Any], typing.Callable[..., typing.Any]], ...
        ] = (),
        **kwargs: typing.Any,
    ) -> typing.Callable[[T], T]:
        """Decorator that marks a function, class, or metaclass as providing
        dataclass-like behavior.
        Example:
            from typing_extensions import dataclass_transform
            _T = TypeVar("_T")
            # Used on a decorator function
            @dataclass_transform()
            def create_model(cls: type[_T]) -> type[_T]:
                ...
                return cls
            @create_model
            class CustomerModel:
                id: int
                name: str
            # Used on a base class
            @dataclass_transform()
            class ModelBase: ...
            class CustomerModel(ModelBase):
                id: int
                name: str
            # Used on a metaclass
            @dataclass_transform()
            class ModelMeta(type): ...
            class ModelBase(metaclass=ModelMeta): ...
            class CustomerModel(ModelBase):
                id: int
                name: str
        Each of the ``CustomerModel`` classes defined in this example will now
        behave similarly to a dataclass created with the ``@dataclasses.dataclass``
        decorator. For example, the type checker will synthesize an ``__init__``
        method.
        The arguments to this decorator can be used to customize this behavior:
        - ``eq_default`` indicates whether the ``eq`` parameter is assumed to be
          True or False if it is omitted by the caller.
        - ``order_default`` indicates whether the ``order`` parameter is
          assumed to be True or False if it is omitted by the caller.
        - ``kw_only_default`` indicates whether the ``kw_only`` parameter is
          assumed to be True or False if it is omitted by the caller.
        - ``field_specifiers`` specifies a static list of supported classes
          or functions that describe fields, similar to ``dataclasses.field()``.
        At runtime, this decorator records its arguments in the
        ``__dataclass_transform__`` attribute on the decorated object.
        See PEP 681 for details.
        """

        def decorator(cls_or_fn):  # type: ignore
            cls_or_fn.__dataclass_transform__ = {
                "eq_default": eq_default,
                "order_default": order_default,
                "kw_only_default": kw_only_default,
                "field_specifiers": field_specifiers,
                "kwargs": kwargs,
            }
            return cls_or_fn

        return decorator
