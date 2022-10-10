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
