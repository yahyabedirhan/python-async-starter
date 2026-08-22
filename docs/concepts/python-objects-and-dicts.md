# Python objects, dicts, and how JavaScript objects compare

Python and JavaScript both let you group related data together, but they
split that job across different constructs. Python keeps class instances
and dictionaries as two separate types with two separate access rules.
JavaScript's plain object does both jobs at once. That difference is easy
to trip over when moving between the two languages, so this doc lays out
each side plainly.

## Python: instances use attribute access, dicts use item access

A class instance in Python only understands **attribute references**,
accessed with a dot. Per the
[Python tutorial](https://docs.python.org/3/tutorial/classes.html):

> "The only operations understood by instance objects are attribute
> references. There are two kinds of valid attribute names: data
> attributes and methods."

```python
class Item:
    def __init__(self, name):
        self.name = name

item = Item("Widget")
item.name       # "Widget", attribute access
item["name"]    # TypeError: 'Item' object is not subscriptable
```

A `dict`, on the other hand, is a **mapping type**, and mapping types are
read with **subscription** (square brackets), not dot notation. Per the
[Python standard types docs](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict):

```python
person = {"name": "Widget"}
person["name"]   # "Widget", item access
person.name      # AttributeError: 'dict' object has no attribute 'name'
```

These are genuinely two different protocols under the hood (`__getattr__`
vs. `__getitem__`), and a plain object of one kind doesn't automatically
support the other's syntax. This is also why `model_dump()` (see
[pydantic.md](pydantic.md)) matters as a real conversion step, not busywork: a Pydantic
model instance and the dict it produces are two different kinds of thing,
one read with dots, the other with brackets, and you have to explicitly
convert between them.

## JavaScript: one construct does both jobs

A plain JavaScript object doesn't draw this line. Per
[MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_objects):

> "An object is a collection of properties, and a property is an
> association between a name (or key) and a value. A property's value
> can be a function, in which case the property is known as a method."

And both access styles work on the same object:

```javascript
const item = { name: "Widget" };
item.name;      // "Widget", dot notation
item["name"];   // "Widget", bracket notation, same property
```

MDN's own docs note bracket notation is really there for names dot
notation can't express: "you cannot use dot notation to access a property
whose name is not a valid JavaScript identifier," for example a name with
a space, or a name held in a variable. But for an ordinary key like
`name`, both notations reach the exact same thing. There's no separate
"dict type" in JavaScript the way Python has one; a plain `{}` already
behaves like a Python dict *and* like a Python class instance,
simultaneously, depending only on which notation you happen to write.

## JavaScript classes don't change any of this

JavaScript does have a `class` keyword, but it doesn't introduce a
separate kind of thing the way Python's class instance vs. dict split
does. Per [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes):

> "Classes are a template for creating objects. They encapsulate data
> with code to work on that data. Classes in JS are built on prototypes
> but also have some syntax and semantics that are unique to classes."

A `class` in JavaScript is a nicer syntax for producing the same kind of
object a `{}` literal produces, not a different data type. An instance's
fields are, per MDN, "similar to object properties," and read exactly the
same way, dot or bracket, either one:

```javascript
class Rectangle {
  constructor(height, width) {
    this.height = height;
    this.width = width;
  }
}

const square = new Rectangle(10, 10);
square.height;    // 10, dot notation
square["height"]; // 10, bracket notation, same value
```

Compare that to Python, where the equivalent class instance flatly
rejects bracket access:

```python
class Rectangle:
    def __init__(self, height, width):
        self.height = height
        self.width = width

square = Rectangle(10, 10)
square.height     # 10, attribute access
square["height"]  # TypeError: 'Rectangle' object is not subscriptable
```

So the JS side of this comparison really only has one axis: plain object
vs. `class` instance is purely a stylistic/organizational choice, both
support both notations identically. Python has two real axes: which
*type* of thing you have (a class instance, or a `dict`) decides which
notation is even legal, regardless of whether that class instance came
from a hand-written class, a Pydantic `BaseModel`, or anything else.

## The practical consequence

Coming from JavaScript, it's natural to expect `.` and `[]` to be mostly
interchangeable, since they are there. In Python, they're not
interchangeable at all, they're two unrelated types with two unrelated
access rules, and mixing them up produces an error rather than just
working. The rule of thumb: if it's a class instance (including a
Pydantic `BaseModel`), use dots. If it's a `dict`, use brackets. Something
like `pagination["skip"]` (see [fastapi.md](fastapi.md)'s dependency injection section) is
bracket access precisely because `pagination_params()` returns a plain
`dict`, not a class instance.
