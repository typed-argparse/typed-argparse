import typed_argparse as tap


class CommonArgs(tap.TypedArgs):
    verbose: bool = tap.arg(default=False, help="Enable verbose log output.")


class FooStartArgs(CommonArgs):
    ...


class FooStopArgs(CommonArgs):
    ...


def run_foo_start(args: FooStartArgs) -> None:
    print(f"Running foo start with {args} {'verbosely!' if args.verbose else ''}")


def run_foo_stop(args: FooStopArgs) -> None:
    print(f"Running foo stop with {args}")


class BarStartArgs(CommonArgs):
    ...


class BarStopArgs(CommonArgs):
    ...


def run_bar_start(args: BarStartArgs) -> None:
    print(f"Running bar start with {args} {'verbosely!' if args.verbose else ''}")


def run_bar_stop(args: BarStopArgs) -> None:
    print(f"Running bar stop with {args}")


def main() -> None:
    tap.Parser(
        tap.SubParserGroup(
            tap.SubParser(
                "foo",
                tap.SubParserGroup(
                    tap.SubParser("start", FooStartArgs, help="Help of foo -> start"),
                    tap.SubParser("stop", FooStopArgs, help="Help of foo -> stop"),
                ),
                help="Help of foo",
            ),
            tap.SubParser(
                "bar",
                tap.SubParserGroup(
                    tap.SubParser("start", BarStartArgs, help="Help of bar -> start"),
                    tap.SubParser("stop", BarStopArgs, help="Help of bar -> stop"),
                    common_args=CommonArgs,
                ),
                help="Help of bar",
            ),
        ),
    ).bind(
        run_foo_start,
        run_foo_stop,
        run_bar_start,
        run_bar_stop,
    ).run()


if __name__ == "__main__":
    main()
