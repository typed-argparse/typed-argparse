from pathlib import Path

import typed_argparse as tap


class Args(tap.TypedArgs):
    src: Path = tap.arg(positional=True, help="Source file")
    dst: Path = tap.arg(positional=True, help="Destination file")


def runner(args: Args):
    print(f"Print copying from '{args.src}' to '{args.dst}'")


def main() -> None:
    tap.Parser(Args).bind(runner).run()


if __name__ == "__main__":
    main()
