## Getting started

Writing apps with `typed_argparse` involves three steps, emphasizing a clear separation of concerns:

1. **Argument definition**: This defines how argument parsing should work.
2. **Business logic**: This defines what your app does.
3. **Bind & run** argument definition with business logic, typically in your top-level `main()` function.

```python title="basic_usage.py"
--8<-- "examples/high_level_api/basic_usage.py"
```

Let's see it in action:

<div class="termy">
```console
--8<-- "examples/high_level_api/basic_usage.console"
```
</div>

Some observations:

- By default, arguments are required and option-like.
  The command line option corresponds to the Python variable name, with underscores replaces by hyphens.
  For instance, `my_arg: str` is specified via `--my-arg <value>` on the command line.
- If an argument has a default it becomes optional (`number_a`).
- If an argument is type-annotated as `Optional[T]` it also becomes optional, but can take the value `None` (`number_b`)
- If an argument is type-annotated as `bool` it becomes as boolean switch.
- If an argument is type-annotated as `List[T]`, it becomes an `nargs="*"` argument, i.e., it allows for zero or more values.


## Positional arguments

By default arguments are option-like, i.e., they are specified as `--some-argument <value>` on the command line.

In order to create positional (unnamed) argument, `positional=True` can be passed to the `tap.arg` function.
For instance:

```python title="positional_arguments.py"
--8<-- "examples/high_level_api/positional_arguments.py"
```

<div class="termy">
```console
--8<-- "examples/high_level_api/positional_arguments.console"
```
</div>


## Flags & renaming

The first argument passed to `tap.arg(...)` can be used to define short option short names, also known as flags.
For instance `foo: str = tap.arg("-f")` introduces the flag `-f` as a shorthand for `--foo`.
Similar to regular argparse, multiple names/flags can be specified.

!!! Note

    As long as only a single letter flag like `-f` is introduced, the original option name (e.g. `--foo`) is still added.
    If any option name is not that is longer than one letter, the original optional name is omitted, i.e., the specified values become an override.
    This feature allows to use different names internally (Python) vs externally (CLI).

```python title="option_names.py"
--8<-- "examples/high_level_api/option_names.py"
```

<div class="termy">
```console
--8<-- "examples/high_level_api/option_names.console"
```
</div>


## Sub-commands

Let's assume we want to write a complex CLI involving many, possible deeply nested, sub-commands (think `git`).
For instance, imagine the an app that takes either `foo` or `bar` as the first level sub-command, and the `foo` sub-command is further split into `start` and `stop`, i.e. the possible command paths are:

```console
$ demo_app foo start
$ demo_app foo stop
$ demo_app bar
```

In `typed_argparse` such a tree-like command structure can be directly modeled as a tree of parsers:

```python title="sub_commands_basic.py"
--8<-- "examples/high_level_api/sub_commands_basic.py"
```

<div class="termy">
```console
--8<-- "examples/high_level_api/sub_commands_basic.console"
```
</div>

Some observations:

- In general a `Parser` or a `SubParser` can either take a `TypedArg` object directly (with leads to no further nesting)
  or a `SubParserGroup` container one or more `SubParser` commands (with adds one level of nesting).
- The general `Parser.bind().run()` pattern is the same as with shallow CLIs.
  The main difference is that sub-commands CLIs bind a runner method for each "leaf" in the argument tree.

!!! Note
    `typed_argparse` internally performs a correctness and completeness check on the functions passed to `Parser.bind()`.
    This makes sure that you cannot accidentally forget to bind a leaf of the argument tree,
    and that all argument types have a matching binding.
    If you plan to write unit tests for your CLI, including a call to `Parser.bind()` is therefore a sensible test that make sure that everything is bound properly.


## Auto-completion

`typed_argparse` builds on top of [`argcomplete`](https://github.com/kislyuk/argcomplete) for auto-completion.
The rule is: If you have `argcomplete` installed, `typed_argparse` detects it and automatically installs the auto-completion.
Check the `argcomplete` documentation how to activate `argcomplete` for your particular shell flavor.
