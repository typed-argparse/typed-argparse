from pathlib import Path

import typed_argparse as tap


class Args(tap.TypedArgs):
    foo: str = tap.arg("-f")
    internal_name: str = tap.arg("--external-name")


def runner(args: Args):
    print(f"args = {args}")


def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
