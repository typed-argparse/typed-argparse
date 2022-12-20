import typed_argparse as tap


class FooStartArgs(tap.TypedArgs):
    ...


class FooStopArgs(tap.TypedArgs):
    ...


class BarArgs(tap.TypedArgs):
    ...


def run_foo_start(args: FooStartArgs) -> None:
    print(f"Running foo start: {args}")


def run_foo_stop(args: FooStopArgs) -> None:
    print(f"Running foo stop: {args}")


def run_bar(args: BarArgs) -> None:
    print(f"Running bar: {args}")


def main() -> None:
    # The tree-like structure of the CLI (foo -> start, foo -> stop, bar)
    # is directly reflected in the parser structure:
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
                BarArgs,
                help="Help of bar",
            ),
        ),
    ).bind(
        run_foo_start,
        run_foo_stop,
        run_bar,
    ).run()


if __name__ == "__main__":
    main()
