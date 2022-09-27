
# Drafts for new API

```py

# App(run_toplevel, CommonArgs).run()

App(
    SubParsers(
        SubParser("foo", run_foo, ArgsFoo, aliases=["co"]),
        SubParser("bar", run_bar, ArgsBar),
    ),
    CommonArgs,
).run()


```

What's weird:
- The fact how CommonArgs is related to ArgsFoo/ArgsBar is not clear.
  It comes after them, but is registered before them in argparser.
- Unclear how to handle non-required subparser? Just add a function top level?
  This is also weird, because information outside the SubParsers definition will
  then determine how the subparser is to be setup.
- What if a subparser doesn't add any additional args? Can it re-use the top level
  command? The problem is that the rule is to always add the args that belong to
  the args class. Re-using the CommonArgs in a subparser would mean that we
  register the same arguments in the subparser as we did in the parent parser.
  This would mean that e.g. `--verbose` exists in both the parent parser and
  the subparser. Awkward. Does argparse even support that, because in the end
  they have to share the same slot in the namespace, and it cannot take two
  different values anyway. Currently we would need a dummy subclass with no
  own args. But perhaps we could check `if subparser_type is parent_type` and
  skip argument addition if needed.


What about

```py
App(
    SubParsers(
        SubParser("foo", run_foo, ArgsFoo, aliases=["co"]),
        SubParser("bar", run_bar, ArgsBar),
        common_args=CommonArgs,
        fallback_run=run_without_command
    ),
).run()


App(
    SubParsers(
        {
            # This is a bit weird, because the primary name is not outside of the SubParser
            # definition, while its aliases are inside. Encoding the aliases in the dictionary
            # key would be hacky.
            "foo": SubParser(run_foo, ArgsFoo, aliases=["co"]),
            "bar": SubParser(run_bar, ArgsBar),
        }
        common_args=CommonArgs,
        fallback_run=run_without_command
    ),
).run()

# Perhaps having a special type for executable would help?
App(
    Execute(MainArgs, run_main)
)

# Now there would be a clear mutual exclusiveness between an Execute and a SubParsers element.
App(
    SubParsers(
        SubParser("foo", Execute(run_foo, ArgsFoo), aliases=["co"]),
        SubParser(
            "bar",
            SubParsers(
                SubParser("create", Execute(run_bar_create, ArgsBarCreate)),
                SubParser("delete", Execute(run_bar_delete, ArgsBarDelete)),
            ),
        ),
        common_args=CommonArgs,
        fallback_run=Execute(CommonArgs, run_without_command),
    ),
)
```

Alternative names for `Execute`:
- `Runnable` => more precise, but long
- `Exec`
- just a tuple?

The `Execute` wrapper helps to tie types to their functions, but is a bit verbose.
Alternatives:
- Infer the args type from the function signature. Sounds doable. The main issue:
  a wrongly annotated function (missing annotations, no first-param-is-type-param)
  can only be detected at runtime, whereas the `Execute` wrapper could verify that
  statically... At least we could type annotate it as `Callable[[TypedArgs], ...]`
  which kind of achieves the same?
- Abstract method `__run__(self)` in the argument classes. Would be concise, but
  then there is no clear separation of concerns between args data and logic.


```py
# For comparison, with infer-type-from-func:
App(run_main)

App(
    SubParsers(
        SubParser("foo", run_foo, aliases=["co"]),
        SubParser(
            "bar",
            SubParsers(
                SubParser("create", run_bar_create),
                SubParser("delete", run_bar_delete),
            ),
        ),
        common_args=CommonArgs,
        # Probably these two need to be mutually exclusive or we must assert that run_without_command
        # consumes a `CommonArgs` type?
        fallback_run=run_without_command,
        # Alternative names:
        run_no_command=...,
        run_with_command=...,
        run_fallback=...,
    ),
)
```

This looks concise, but is it a bit too much magic? Seeing the involved types requires to
jump to the function definitions...


```py

# For comparison, with args types only:
App(MainArgs)

App(
    SubParsers(
        SubParser("foo", FooArgs, aliases=["co"]),
        SubParser(
            "bar",
            SubParsers(
                SubParser("create", BarCreateArgs),
                SubParser("delete", BarDeleteArgs),
            ),
        ),
        common_args=CommonArgs,
        required=False,
    ),
)
```

Somehow this feels a bit more obvious because it emphasizes the involved arg types,
which makes it easier to see their relation ship (e.g. that FooArgs need to be a
subclass of CommonArgs). Since the common args cannot be specified via a function
it is more consistent now, that everything is based on types, not a mix of functions
and one type.

A possible "weak coupling" of the arg types to the runnable would be:

```py
class Args(TypedArgs):
    foo: str

    __run__ = run_main


def run_main(args: Args):
    ...
```

One could even introduce an abstract base type `CommandArgs` that derives from `TypedArgs`
and enforces that the `__run__` slot is defined.

However: This creates an ugly dependency from args types to the full runtime code. This
would for instance imply that `Args` cannot be placed in a small lightweight module that
has minimal dependencies, and can be imported from everywhere. Doing so would mean that
the args module would have to import from the fat executable module. This not only means
that there cannot be a lightweight args module, but also creates a potential for cyclic
dependencies (executable module wants to import the args module, which needs to import
the executable module).

=> Bad idea.

One alternative would be to introduce the coupling via a mapping, perhaps only passed
in the `.run()` method?

```py
App(
    SubParsers(
        SubParser("foo", FooArgs, aliases=["co"]),
        SubParser(
            "bar",
            SubParsers(
                SubParser("create", BarCreateArgs),
                SubParser("delete", BarDeleteArgs),
            ),
        ),
        common_args=CommonArgs,
        required=False,
    ),
).run({
    FooArgs: run_foo,
    BarCreateArgs: run_bar_create,
    BarDeleteArgs: run_bar_delete,
})
```

Pros:
- This fully decouples parsing from execution. I.e., `App.parse_args()` would be possible
  without having to "connect" executables for no reason.

Cons:
- Since the mapping isn't done exactly where the args are introduced above, the mapping could
  be incomplete. Completeness of the mapping cannot be verified statically anymore. The worst
  case would be that a missing mapping entry is only detected once it is used. This would
  make it very easy to break a CLI by introducing it above and forgetting to introduce the
  corresponding mapping. To mitigate that, the `run` method could performance an up-front
  completeness check, whether all involved types are included in the mapping. Then it would
  be at least detected very prominently at runtime (CLI not usable in general...).

Perhaps it would even make sense to use a builder pattern to disentangle that check for
the actual execution:

```py
App(
    ...
).with_executables({
    FooArgs: run_foo,
    BarCreateArgs: run_bar_create,
    BarDeleteArgs: run_bar_delete,
}).run()

# In the minimal case:
App(Args).with_executables({Args: run_main}).run()

# Alternative namings
Parser(Args).build_app({Args: run_main}).run()
Parser(Args).into_app({Args: run_main}).run()
Parser(Args).make_app({Args: run_main}).run()
Parser(Args).make_executable({Args: run_main}).run()

# Perhaps a type-safe mapping would require:
Parser(
    ...
).build_app(
    (FooArgs, run_foo),
    (BarCreateArgs, run_bar_create),
    (BarDeleteArgs, run_bar_delete),
).run()


# Or even?
Parser(
    ...
).build_app(
    FooArgs.bind_to_func(run_foo),
    BarCreateArgs.bind_to_func(run_bar_create),
    BarDeleteArgs.bind_to_func(run_bar_delete),
).run()
```


# Instruction order to allow for lazy loading

```py
# First approach
Parser(...).build_app(...).run()
```

Issue: binding happens before `argparse.parse_arg` (inside `run`).

Therefore lazy loading is pointless. Arg parsing must happen before binding.
On the other hand we want to execute the binding directly on the parser to
make sure that the bindings fit to the parser structure.

Drafts:

```py
# This way doesn't enforce what happens first
parser = Parser(...)
parsed_args_wrapper = parser.parse_args()
parsers.bind(...).run(parsed_args_wrapper)

# Better?
parser = Parser(...)
parsed_args = parser.parse_args()
parsed_args.bind(...).run()

parser = Parser(...)
args = parser.parse_args()
args.make_app(...).run()

# minimal
Parser(...).parse_args().make_app(...).run()

Parser(...).parse_args().make_app(parser.build_mapping(...)).run()
Parser(...).parse_args().run(parser.bind(...))

# Issue: Cannot be written in a single line, because `parser` is needed twice...

parser = Parser(...)
args = parser.parse()
bindings = parser.bind()
args.run(bindings)

Parser(...).parse_args().run(lambda parser: parser.bind(...))

# With a free function it looks relatively nice:
Parser(...).parse_args().run(make_bindings)

# With a single command
Parser(Args).parse_args().run(lambda parser: parser.bind(tap.Binding(Args, runner)))

# A bit clumsy having the `parser` twice in the lambda... And if `parser` exists as
# a local variable people may actually drop the passed-in parser `lambda _: parser.bind(...)`.

# What about:
Parser(Args).parse_args().run(lambda: [tap.Binding(Args, runner)])
# => no way to verify bindings?

# What about:
tap.run(parser.parse_args(), parser.bind(...))
# - Evaluation order guarantees args are parsed first.
# - No wrapper type needed for args, just return plain TypedArgs.

# But it would be still up to the user to order everything correctly:
args = parser.parse_args()
import runner
bindings = parser.bind(tap.Binding(Ars, runner))
tap.run(args, bindings)

# And: No way to write in one line. Minimal case:
parser = Parser(Args)
tap.run(parser.parse_args(), parser.bind(tap.Binding(Args, runner)))

# Then perhaps a lambda again?
tap.run(Parser(Args), lambda parser: parser.bind(...))

# This is basically just switching a run method for a free-floating run...
Parser(Args).run(lambda parser: parser.bind(...))

# Ah but with the difference, that the parse_args() call is no longer explicit
# but implicit, which reduces the need for a wrapper type... This at least minimized
# the minimal example to:
Parser(Args).run(lambda p: p.bind(tap.Binding(Args, runner)))
```



# How to support mutually exclusive params?

Most straightforward:

```py
class Args(TypedArgs):
    a: Optional[int]
    b: Optional[str]
    c: Optional[str]

    foo: Optional[int]
    bar: Optional[str]

    __config__ = ParamsConfig(
          mutually_exclusive_groups=[
              ("a", "b", "c"),
              ("foo", "bar"),
          ],
    )
```

What is not so great about that is that the mutual-exclusiveness isn't reflected in
the type system. An alternative:

```py
class Args(TypedArgs):
    a_or_b_or_c: Union[...] = mutually_exclusive_params(
        param("-a", ...),
        param("-b", ...),
        param("-c", ...),
    )
```

This isn't entirely straightforward, because the we would have to generate a tagged union
to encode which of the branches was selected. Note that `Union[int, str, str]` doesn't make
sense.

Perhaps the "type unification" of mutually exclusive params could relatively easily be
solved on user side for instance by adding a member method/property `Args.a_or_b_or_c` that
internally does the assert and branching.


# Argparse checks


## Does it matter whether arguments are registered before/after subparsers?

```py
import argparse


for add_before in [True, False]:
    print(f"\n{add_before = }")

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        help="Available sub commands",
        dest="mode",
        required=True,
    )

    if add_before:
        parser.add_argument("--verbose", action="store_true", help="Verbose")

    parser_foo = subparsers.add_parser("foo")
    parser_foo.add_argument("file", type=str)

    parser_bar = subparsers.add_parser("bar")
    parser_bar.add_argument("--src", required=True)
    parser_bar.add_argument("--dst", required=True)

    if not add_before:
        parser.add_argument("--verbose", action="store_true", help="Verbose")

    parser.print_help()
    parser.parse_args(["--verbose", "foo", "myfile"])
```

Conclusion: argparse treats them the same. They always come before subparser args in terms of order,
so it makes a bit more sense in the code to define them before as well...


## Does it make sense to have sequential subparsers?

```py
import argparse

parser = argparse.ArgumentParser()

subparsers_a = parser.add_subparsers(
    help="Available sub commands",
    dest="mode",
    required=True,
)

parser_foo = subparsers_a.add_parser("foo")
parser_bar = subparsers_a.add_parser("bar")

# This throws
subparsers_b = parser.add_subparsers(
    help="Other available sub commands",
    dest="other",
    required=True,
)

other_parser_foo = subparsers_b.add_parser("other_foo")
other_parser_bar = subparsers_b.add_parser("other_bar")

parser.print_help()
# parser.parse_args(["--verbose", "foo", "myfile"])
```

As expected, argparse throws an exception when adding another subparser.

Conclusion: It makes sense to restrict the API to a single subparser branching (per level).


## Is it possible to fully hide the `dest` name of subparser?

```py
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("other_position", help="other positional")

subparsers_a = parser.add_subparsers(
    #title="mytitle",
    #description="my description",
    help="Available sub commands",
    #dest="__internal__cryptic__dest__",
    #metavar="mode",
    required=False,
)

parser_foo = subparsers_a.add_parser("foo")
parser_bar = subparsers_a.add_parser("bar")

parser.print_help()
# parser.parse_args(["wrong"])
parser.parse_args(["other_positional", "foo"])
```

Without metavar:
```
usage: ipython [-h] {foo,bar} ...

positional arguments:
  {foo,bar}   Available sub commands

optional arguments:
  -h, --help  show this help message and exit
usage: ipython [-h] {foo,bar} ...
ipython: error: argument __internal__cryptic__dest__: invalid choice: 'wrong' (choose from 'foo', 'bar')
```

```
usage: ipython [-h] mode ...

positional arguments:
  mode        Available sub commands

optional arguments:
  -h, --help  show this help message and exit
usage: ipython [-h] mode ...
ipython: error: argument mode: invalid choice: 'wrong' (choose from 'foo', 'bar')
```

or when omitting the arg:

```
## -- End pasted text --
usage: ipython [-h] mode ...

positional arguments:
  mode        Available sub commands

optional arguments:
  -h, --help  show this help message and exit
usage: ipython [-h] mode ...
ipython: error: the following arguments are required: mode
```

Setting the title only leads to:

```
usage: ipython [-h] {foo,bar} ...

optional arguments:
  -h, --help  show this help message and exit

mytitle:
  {foo,bar}   Available sub commands
usage: ipython [-h] {foo,bar} ...
ipython: error: the following arguments are required: __internal__cryptic__dest__
```

Setting title and description:

```
usage: ipython [-h] other_position {foo,bar} ...

positional arguments:
  other_position  other positional

optional arguments:
  -h, --help      show this help message and exit

mytitle:
  my description

  {foo,bar}       Available sub commands
usage: ipython [-h] other_position {foo,bar} ...
ipython: error: the following arguments are required: other_position, __internal__cryptic__dest__
```

Conclusion: Setting title and description feels a bit unnecessary, because it moves the
`<METAVAR> <HELP>` line into its own section, which makes the line a bit weird (I assume
there can never be another `<METAVAR> <HELP>` line in that section as is the case for other
sections like `positional arguments`). And if the metavar would not enumerate the values
the line would become something rather uninformative like `<MODE>   Available modes`.

Conclusion: Setting `metavar` seems to hide the internal name. But comes at the cost of
not seeing at all which values are allowed. This basically means that one should never set
metavar unless one enumerates the allowed values in the help text...

