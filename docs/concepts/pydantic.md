# Pydantic

The data-validation library FastAPI uses under the hood for request bodies,
response models, and (via `fastapi`'s own wrapping) query/path parameter
validation. See [docs/concepts/python-type-hints.md](python-type-hints.md) first, since this doc
assumes you know what a type hint is and what a DSL is, and focuses on what
Pydantic specifically does with that feature.

## What Pydantic actually does

A Pydantic model is a normal-looking Python class with type-hinted fields:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
```

Per Pydantic's own docs
([pydantic.dev/docs/validation/latest/get-started](https://pydantic.dev/docs/validation/latest/get-started/)),
it's described as "the most widely used data validation library for
Python," and the mechanism is exactly what the class above suggests:

> "with Pydantic, schema validation and serialization are controlled by
> type annotations; less to learn, less code to write, and integration with
> your IDE and static analysis tools."

Pydantic reads those type hints at class-definition time and builds a
validator out of them. Handing it a dict from a JSON body, it checks each
field's type, converts what it reasonably can (a JSON `"9.99"` string
becomes a Python `9.99` float, for instance), and raises a structured error
listing exactly which fields failed and why if something doesn't fit.

## Performance: it's not pure Python

Worth noting since it's a common assumption people carry over from "Python
is slow" folklore: Pydantic's docs state plainly that "Pydantic's core
validation logic is written in Rust" (same source as above). The actual
validation work happens in compiled, non-Python code, which is why it's fast
enough to run on every single request without becoming the bottleneck.

## Getting a plain dict back out: `model_dump()`

A `BaseModel` instance isn't a plain Python object with generic dict-like
behavior. `model_dump()` is a method Pydantic itself adds to every
`BaseModel` subclass, not something ordinary Python classes get for free.
Per [Pydantic's own API docs](https://docs.pydantic.dev/latest/api/base_model/):

> "Generate a dictionary representation of the model, optionally
> specifying which fields to include or exclude."

So `item.model_dump()` turns a model instance back into a plain `dict`,
the reverse direction of what validation does when a dict comes in.
Handing that dict's contents into another call with `**item.model_dump()`
(Python's dictionary-unpacking syntax) is a common pattern for copying
one model's fields into a new instance, similar in effect to spreading an
object in JavaScript, but this is a Pydantic method, not something every
Python object supports.

## How this feeds into FastAPI specifically

One `class Item(BaseModel): name: str; price: float` declaration feeds four
separate things in a FastAPI app, all derived from the same source instead
of kept in sync by hand:

1. **Validation**: Pydantic rejects malformed request bodies before your
   function even runs.
2. **Serialization**: the same model converts your Python object back to
   JSON for the response.
3. **Editor support**: your IDE knows `item.name` exists and is a `str`,
   because it's reading the same class definition.
4. **OpenAPI docs**: FastAPI turns the model into a JSON Schema, which
   Swagger UI (`/docs`) renders as a form showing exactly which fields are
   required and what type each one is.

That's the concrete shape of "FastAPI's core feature is type hints doing
four jobs at once." Pydantic is the piece that actually turns the type
hints into a working validator; FastAPI is the piece that wires that
validator into request handling and the auto-generated docs.
