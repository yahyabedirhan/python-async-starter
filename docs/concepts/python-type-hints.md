# Python type hints, and what "editor support" and "DSL" mean

FastAPI's whole pitch rests on one small Python feature, type hints,
getting reused for several jobs at once (validation, docs, editor support).
This doc covers the feature itself, in isolation from any specific library.
See [docs/concepts/pydantic.md](pydantic.md) for how Pydantic specifically builds on
top of it.

## What a type hint actually is

A type hint is an annotation you can attach to a variable, a function
argument, or a return value, saying what type it's expected to be:

```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```

The critical thing to understand: **Python itself does nothing with this at
run time.** The official docs state it directly, at
[docs.python.org/3/library/typing.html](https://docs.python.org/3/library/typing.html):

> "The Python runtime does not enforce function and variable type
> annotations. They can be used by third party tools such as type checkers,
> IDEs, linters, etc."

So `greet(123)` runs just fine and returns `"Hello, 123"`. Python never
checks that `123` isn't a `str`. The type hint is purely *metadata* sitting
next to your code. It only becomes useful because other tools choose to read
it and act on it.

## What "editor support" concretely means

"Editor support" isn't a vague marketing phrase. It means specific,
concrete things your editor (VS Code, PyCharm, etc.) can do *because* it can
read those type hints:

- **Autocomplete**: if a function parameter is typed as `Item` (a class with
  `name` and `price` fields), your editor knows `item.` should suggest
  `.name` and `.price`. It doesn't have to guess or scan your whole
  codebase for hints.
- **Inline error squiggles**: if you write `item.pric` (typo) or pass a
  `str` where an `int` is expected, the editor flags it *before you run
  anything*, the same way a spell-checker underlines a typo in a word
  processor.
- **Safe refactors**: rename a field on a model, and the editor can find
  every place that reads it, because it can trace the type through your
  code instead of just grepping for a matching name.

None of this is Python running your code. It's a separate program (a
**type checker**, like `mypy` or `pyright`) doing static analysis: reading
your source text and reasoning about types without executing anything. The
Python docs' own phrase for these consumers is "third party tools such as
type checkers, IDEs, linters" (same page as above); editors just embed one
of those type checkers and show its output inline as you type.

## What a "DSL" is, and why type hints avoid needing one

**DSL** stands for **Domain-Specific Language**, a small language (or
language-like syntax) built for one narrow job, as opposed to a
general-purpose language like Python or JavaScript. It doesn't have to mean
a whole new file format; a DSL can live *inside* a general-purpose language
as a set of function calls and objects that only make sense together, for
one purpose.

A concrete example: JavaScript's `zod` or `joi` validation libraries. You
don't validate a JS object using JavaScript's own type system (JavaScript
doesn't really have one at runtime). Instead you write a *separate
description* of the shape, in that library's own vocabulary:

```javascript
const schema = z.object({
  name: z.string(),
  price: z.number(),
});
```

That `z.object({...})` call is a DSL: a mini-language for describing shapes,
distinct from the language you're writing the rest of your app in. It works,
but now you maintain **two parallel descriptions** of the same data: the
TypeScript `interface Item { name: string; price: number }` you'd write for
editor support, *and* this separate `zod` schema for runtime validation.
Nothing forces those two descriptions to stay in sync; they're just two
files a human has to remember to update together. Django REST Framework's
`serializers.Serializer` classes are the same pattern in Python: a
declarative validation language that exists parallel to, not derived from,
your actual Python types.

Python's approach (via type hints, and libraries like Pydantic that read
them) avoids this duplication: the type hint you'd write for editor support
anyway is the *same* declaration a validation library reads at run time.
One declaration, not two vocabularies to keep in sync.

## Types are runtime values in Python

This is the fact that makes something like `response_model=list[Item]`
possible as ordinary Python, not special FastAPI syntax. In Python, a
class is itself an object that exists while the program runs, not just a
compile-time label the language throws away. Per the
[Python language reference](https://docs.python.org/3/reference/datamodel.html):

> "Objects are Python's abstraction for data. All data in a Python
> program is represented by objects or by relations between objects."

And specifically for classes:

> "Classes are callable. These objects normally act as factories for new
> instances of themselves..."

So `Item` (a class) is a real object sitting in memory, the same way a
string or a number is. It can be passed as a function argument, assigned
to a variable, stored in a list, exactly like any other value. That's why
`response_model=list[Item]` type-checks and runs fine: `list[Item]` isn't
being "used as a type" in some special way, it's just an ordinary value
being passed as a keyword argument, the same as passing `42` or `"hello"`
would be.

This is a genuine difference from TypeScript, where types are erased
entirely before the code ever runs; there's no `SomeInterface` object you
could pass around as a value at runtime, because by the time the code
executes, the type annotations don't exist anymore. Python's annotations
stick around and can be inspected, passed, and acted on by code like
Pydantic or FastAPI, precisely because the things they refer to (classes)
were always real, live objects to begin with, not something the language
invented purely for a type-checking pass and threw away afterward.
