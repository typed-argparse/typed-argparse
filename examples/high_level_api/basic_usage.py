from typing import List, Optional

import typed_argparse as tap


class Args(tap.TypedArgs):
    foo: str = tap.arg(help="A foo")
    num: Optional[int] = tap.arg(help="A number")
    files: List[str] = tap.arg(help="Some files")


def runner(args: Args):
    print(args)


def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
