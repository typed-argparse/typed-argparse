from enum import Enum

import typed_argparse as tap


class Color(Enum):
    RED = 1
    GREEN = "green"

    def __str__(self) -> str:
        return str(self.value)


class Make(Enum):
    BIG = 1
    SMALL = "small"


class Args(tap.TypedArgs):
    color: Color
    make: Make


def runner(args: Args):
    print(f"Running my app with args:\n{args}")


def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
