# Python concurrency: threads, processes, the GIL, and asyncio

How Python's actual primitives (OS threads, OS processes) interact with a
CPython-specific wrinkle (the GIL), and how that explains why `asyncio`
exists and behaves the way it does. See [docs/concepts/concurrency-models.md](concurrency-models.md)
first for what "threads," "processes," and "event loop" mean in general.
This doc is Python's specific take on those general ideas, from the ground
up. [docs/concepts/python-event-loop.md](python-event-loop.md) goes one level deeper still, into
the event loop's own internal scheduling mechanics and a direct comparison
with JavaScript's event loop.

## The starting primitives: threads and processes

Python gives you the same two OS-level primitives any language does, an
OS **thread** (`threading` module) and an OS **process** (`multiprocessing`
module), with the same general trade-offs from
[docs/concepts/concurrency-models.md](concurrency-models.md): a process is heavier but fully
isolated (own memory space), a thread is lighter but shares memory with
every other thread in its process. In most languages, that's most of the
story: pick threads for lighter-weight concurrency, processes when you need
isolation or want to spread work across CPU cores.

Python has one more piece that changes this calculation significantly.

## The Global Interpreter Lock (GIL)

CPython (the standard Python interpreter) has a **Global Interpreter Lock
(GIL)**. The Python glossary's own definition
([docs.python.org/3/glossary.html#term-global-interpreter-lock](https://docs.python.org/3/glossary.html#term-global-interpreter-lock)):

> "The mechanism used by the CPython interpreter to assure that only one
> thread executes Python bytecode at a time."

So even if you spin up ten OS threads in a Python program, only one of them
is ever actually executing Python code at any given instant.

**Why CPython has it**: the GIL exists specifically to simplify CPython's
internals, by making built-in types like `dict` safe against concurrent
access "at the expense of much of the parallelism afforded by
multi-processor machines" (same source as above).

### What it implies in practice

Threads still help for I/O-bound work, because the GIL is released while a
thread is blocked waiting on I/O, but they give you essentially nothing
for CPU-bound work (crunching numbers), which is why CPU-heavy Python
workloads reach for **separate processes** (`multiprocessing`), not
threads, to get real parallelism. Separate processes each get their own
interpreter and their own GIL, so they genuinely run on different CPU
cores at once. The GIL only limits parallelism *within* a single process.

This directly answers the natural question of "so which primitive do I
reach for": for CPU-bound work, processes; for I/O-bound work, either
threads or (as covered below) `asyncio`.

### Worth knowing exists

Python 3.13 added an experimental build option to disable the GIL, per
[PEP 703](https://peps.python.org/pep-0703/) (referenced from the same
glossary page above). Not relevant to this project's Python 3.12 pin, but
worth knowing the GIL isn't necessarily a permanent fact about Python going
forward.

## Why using `asyncio` instead of threads costs you almost nothing

This is the direct link between the GIL and `asyncio`'s existence. You
might expect that switching from many threads to `asyncio`'s single thread
would cost you something, namely real parallel execution across multiple
CPU cores. In Python specifically, it doesn't, because Python's threads
never had that to begin with: the GIL already stops them from running
Python code in true parallel, with or without `asyncio`. So for I/O-bound
work, threads and `asyncio` end up delivering roughly the same thing in
Python. In a language without a GIL, this wouldn't be true. Threads there
really would give you parallelism an event loop can't, making the choice
between them a much bigger trade-off than it is in Python.

## How `asyncio` actually works: coroutines, Tasks, and scheduling

An `async def` function is a **coroutine function**. Calling one doesn't
run it. It returns a **coroutine object**, a paused, not-yet-started unit
of work. Per Python's own docs
([docs.python.org/3/library/asyncio-task.html](https://docs.python.org/3/library/asyncio-task.html)):

> "Nothing happens if we just call `nested()`. A coroutine object is
> created but not awaited, so it won't run at all."

Nothing actually runs until something drives that coroutine object
forward, either by `await`-ing it directly, or by wrapping it in a
**`Task`** with `asyncio.create_task()`. A `Task` is what actually gets
scheduled onto the event loop and run concurrently with everything else
in flight.

This has a direct, concrete consequence for how you write concurrent code:
`await`-ing one coroutine, then another, doesn't run them at the same
time. It runs the first one to completion, *then* starts the second. The
docs' own example shows this with real timings.

**Sequential: `await` one coroutine, then the next.**

```python
async def main():
    print(f"started at {time.strftime('%X')}")
    await say_after(1, 'hello')
    await say_after(2, 'world')
    print(f"finished at {time.strftime('%X')}")
```

> "The following snippet of code will print 'hello' after waiting for 1
> second, and then print 'world' after waiting for *another* 2 seconds",
> for a total of **3 seconds** (`started at 17:13:52` → `finished at 17:13:55`
> in the docs' own sample run).

**Concurrent: wrap each one in a `Task` first, *then* await.**

```python
async def main():
    task1 = asyncio.create_task(say_after(1, 'hello'))
    task2 = asyncio.create_task(say_after(2, 'world'))
    await task1
    await task2
```

The docs note the difference directly: "the expected output now shows
that the snippet runs 1 second faster than before," for a total of
**2 seconds** (the two 1s/2s waits overlap instead of stacking).

The mental model: `await` on a plain coroutine doesn't just "wait for"
something already running. It's what *starts and drives* that coroutine,
and it won't return control to the rest of your code until that specific
coroutine finishes. Getting several things running at once requires
explicitly saying so, either with `create_task()` (start it now, in the
background) or with `asyncio.gather()`:

> "Run awaitable objects in the *aws* sequence concurrently." (same docs
> page as above)

`gather()` takes bare coroutines and starts them itself, so
`asyncio.gather(fetch_a(), fetch_b())` gets you concurrency directly,
without a separate `create_task()` call first. Same job as `create_task()`
plus `await`, just for a whole batch at once.

## Comparison with JavaScript

Everything above stands on its own. This section is specifically for
carrying over intuition from JavaScript's `async`/`await`/`Promise` model,
since several assumptions from there don't transfer cleanly. Two sibling
docs go deeper on the JS side specifically: [docs/concepts/javascript-event-loop.md](javascript-event-loop.md)
covers the call stack/microtask/macrotask mechanics underneath `async`/
`await`, and [docs/concepts/javascript-runtimes.md](javascript-runtimes.md) covers how V8, Node,
Deno, Bun, and WebKit each implement that event loop differently.

### No engine/runtime split in Python

`javascript-runtimes.md` draws a distinction worth borrowing directly:
JavaScript separates the **engine** (V8, JavaScriptCore, which parse and
run JS per the ECMAScript spec, with no concept of an event loop, timers,
or I/O on its own) from the **runtime** (Node, Deno, Bun, or a browser,
which embeds an engine and supplies the actual event loop plus host APIs
like `setTimeout` and `fetch` on top of it). That split is exactly why the
same JS code can behave slightly differently under Node vs. Deno vs. a
browser even with an identical engine underneath. The event loop isn't
part of the language, it's provided by whichever runtime is hosting it.

Python has no equivalent split. `asyncio` isn't a separate runtime layered
on top of a language-only engine. It's a module in Python's own standard
library, built and shipped by the same project as the interpreter itself
(CPython). There's no scenario analogous to "the same Python engine,
different event loop implementation depending on which runtime embeds
it." CPython and `asyncio` are one project, not an engine with several
competing runtimes built around it. Worth naming explicitly since it's
the kind of structural difference that's easy to assume carries over
silently when it doesn't.

### Terminology, mapped

| JavaScript | Python `asyncio` | What it is |
|---|---|---|
| `async function` | coroutine function (`async def`) | a function whose body can pause at await points |
| `Promise` | `asyncio.Future` | "represents an eventual result of an asynchronous operation," per [docs.python.org/3/library/asyncio-future.html](https://docs.python.org/3/library/asyncio-future.html); the actual behavioral match: both are a live, already-in-motion handle you can check on or await |
| calling an async function directly | `asyncio.create_task(coro())` | what actually starts the work running concurrently, in the background |
| `Promise.all([...])` | `asyncio.gather(...)` | run several awaitables concurrently, wait for all of them |
| `await` | `await` | pause the current coroutine until the awaited thing resolves |

Deliberately not a row above for "the Promise returned by calling an
async function" mapped to "the coroutine object returned by calling one."
They occupy the same *position* (both are literally what the function call
returns), but they are not equivalent, and a table row implying they are
would misstate the most important behavioral difference in this whole
comparison, covered next. A JS Promise is a live, eager handle the instant
it's returned; a Python coroutine object is inert, not even started, until
something drives it. The row that's actually true to "what plays the
Promise's role" is the `Future` row above. A coroutine object on its own
doesn't play that role at all.

### Python coroutines are lazy, Promises are eager

In JavaScript, calling an async function (or `fetch()`) starts the actual
work *immediately*. The Promise you get back is just a handle for
checking on something already in flight:

- **[MDN's `async function` page](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function):**
  "Top-level code, up to and including the first `await` expression (if
  there is one), is run synchronously. In this way, an async function
  without an await expression will run synchronously." In other words,
  calling an async function runs its body immediately, right up to the
  first `await`, before control ever returns to whoever called it.
- **[MDN's `Promise()` constructor page](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/Promise):**
  "The executor is called synchronously (as soon as the Promise is
  constructed)." Same fact from the other angle: the code that actually
  *does* the work inside a Promise runs the instant the Promise object is
  created, not later when something calls `.then()` or `await`s it.

So this is idiomatic, working JS:

```javascript
const p1 = fetchA(); // fetchA's request has already started
const p2 = fetchB(); // fetchB's request has already started too — concurrently with A
const [a, b] = await Promise.all([p1, p2]);
```

Even `const [a, b] = [await fetchA(), await fetchB()]` written slightly
differently can end up concurrent in JS, because the calls themselves
already kicked off the work before either `await` runs.

Python's coroutines don't work this way. As established above, calling a
coroutine function does *nothing* until something drives it forward with
`await` or `create_task()`. JS gives you the concurrent version by
default, almost by accident, because calling the function was already
enough to start it; Python requires you to opt in.

### `asyncio.gather()` vs. `Promise.all()`

These two are the closest 1:1 match in the whole comparison.
`Promise.all()` per [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all):

> "It is typically used when there are multiple related asynchronous
> tasks that the overall code relies on to work successfully — all of
> whom we want to fulfill before the code execution continues."

Same job, same shape (pass in a collection, get back a collection of
results once everything's done) as `asyncio.gather()` above. The
eager-vs-lazy difference still applies to how each one gets *fed*, though:
`Promise.all()` receives already-started Promises (the work began the
instant each async function was called), while `asyncio.gather()` receives
bare, not-yet-started coroutines and starts them itself. That's why
`gather()` is one of the few places Python's laziness gets handled for you
automatically, without you needing to reach for `create_task()` first.
