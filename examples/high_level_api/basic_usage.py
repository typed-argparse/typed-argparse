from typing import List, Optional

import typed_argparse as tap


# 1. Argument definition
class Args(tap.TypedArgs):
    my_arg: str = tap.arg(help="some help")
    number_a: int = tap.arg(default=42, help="some help")
    number_b: Optional[int] = tap.arg(help="some help")
    verbose: bool = tap.arg(help="some help")
    names: List[str] = tap.arg(help="some help")


# 2. Business logic
def runner(args: Args):
    print(f"Running my app with args:\n{args}")


# 3. Bind argument definition + business logic & run
def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
