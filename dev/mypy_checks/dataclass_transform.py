from typing_extensions import dataclass_transform


@dataclass_transform(kw_only_default=True)
class ModelBase:
    def __init__(self, **kwargs: object):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CustomerModel(ModelBase):
    id: int
    name: str


class CustomerModelSub(CustomerModel):
    extended: bool


def checks() -> None:
    model1 = CustomerModel(id=42, name="foo")
    print(model1.__dict__)

    model2 = CustomerModelSub(id=42, name="foo", extended=True)
    print(model2.__dict__)


if __name__ == "__main__":
    checks()
