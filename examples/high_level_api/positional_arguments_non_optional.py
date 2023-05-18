from pathlib import Path
from typing import List

import typed_argparse as tap


class Args(tap.TypedArgs):
    sources: List[Path] = tap.arg(
        positional=True,
        help="Source path(s)",
        nargs="+",
    )
    dest: Path = tap.arg(
        positional=True,
        help="Destination path",
    )


def runner(args: Args):
    print(f"Moving sources '{repr(args.sources)}' to dest '{repr(args.dest)}'")


def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
