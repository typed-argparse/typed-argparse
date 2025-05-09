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

By default arguments are option-like, i.e., if the field name is `some_argument` can be specified as `--some-argument <value>` on the command line.

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


## Multiple positional arguments

Positional arguments can be turned into lists:

- `nargs=*` corresponds to a list that can be empty, i.e., it is optional to specify any arguments.
- `nargs=+` corresponds to a list that cannot be empty, i.e., at least one argument must be given.

Using `nargs` implies that in terms of the type signature the arguments becomes a `some_argument: List[T]` instead of `some_argument: T`.
Correct usage is verified by type_argparse's type signatures.

For example the following would result in similar semantics like `mv` (multiple but non-zero inputs, single output):

```python title="positional_arguments.py"
--8<-- "examples/high_level_api/positional_arguments_non_optional.py"
```

<div class="termy">
```console
--8<-- "examples/high_level_api/positional_arguments_non_optional.console"
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
  or a `SubParserGroup` container which in turn contains one or more `SubParser` commands (with adds one level of nesting).
- The general `Parser.bind().run()` pattern is the same as with shallow CLIs.
  The main difference is that sub-commands CLIs bind a runner method for each "leaf" in the argument tree.

!!! Note
    `typed_argparse` internally performs a correctness and completeness check on the functions passed to `Parser.bind()`.
    This makes sure that you cannot accidentally forget to bind a leaf of the argument tree,
    and that all argument types have a matching binding.
    If you plan to write unit tests for your CLI, including a call to `Parser.bind()` is therefore a sensible test that makes sure that everything is bound properly.


## Common arguments in sub-commands

If some arguments should be shared between multiple sub-commands, provide a base class with those arguments and have the class defining the arguments subclass this.

In the example below, the common argumen is `--verbose` and `CommonArgs` just describes this argument.
There are two options for how these options need to be passed on the command line.
In the example, the two sub-commands `foo` and `bar` use the two options different options:

- For `foo` the `CommonArgs` are just used as subclass and not passed via the `common_args=...` argument to the subparser group.
  The common arguments will be added to each command individually, i.e., usage becomes `<myapp> foo start --verbose` and `<myapp> foo stop --verbose`.
- For `bar` the `CommonArgs` are used as subclass and additionally passed as the `common_args=...` argument to the subparser group.
  The common argument will be added at the parent level, i.e., usage becomes `<myapp> bar --verbose start` and `<myapp> bar --verbose stop`.


```python title="sub_commands_common_arguments.py"
--8<-- "examples/high_level_api/sub_commands_common_arguments.py"
```

Compare the help output for the two different sub-commands:

<div class="termy">
```console
--8<-- "examples/high_level_api/sub_commands_common_arguments.console"
```
</div>


## Auto-completion

`typed_argparse` builds on top of [`argcomplete`](https://github.com/kislyuk/argcomplete) for auto-completion.
The rule is: If you have `argcomplete` installed, `typed_argparse` detects it and automatically installs the auto-completion.
Check the `argcomplete` documentation how to activate `argcomplete` for your particular shell flavor.


## Enums

Passing `Enum` values as argument is straight forward.
They are handled just like any other type.

There is just a single caveat, when it comes to the help output.
If the default `__str__` method of the enum is used, the help output will not display the values bur rather the names.
A simple solution is hence to overwrite `__str__` so that the value is printed.
(Note: From Python 3.11 onwards, the `StrEnum` class does that automatically.)

For Python versions *prior to 3.12* it also makes sense to overwrite `__repr__` to
print the value, as `repr` is used to generate the error output.


```python title="enum_arguments.py"
--8<-- "examples/high_level_api/enum_arguments.py"
```

Compare the help output for the two different enums:

<div class="termy">
```console
--8<-- "examples/high_level_api/enum_arguments.console"
```
</div>