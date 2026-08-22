# FastAPI

## What it is

A Python web framework for building APIs, built on top of Starlette (ASGI web
toolkit) and Pydantic (data validation). It natively supports `async def`
route handlers, which matters for this project's async IO goals later on.

## Official recommended setup

Per the official docs (fastapi.tiangolo.com):

```bash
uv add "fastapi[standard]"
```

The `[standard]` extra pulls in the commonly-needed pieces so you don't
assemble them by hand: `uvicorn[standard]` (the ASGI server that actually
runs the app), `fastapi-cli` (the `fastapi` command), plus `httpx`,
`jinja2`, `python-multipart`, `email-validator`.

No special folder structure is required for a small project. A single
`main.py` with an `app = FastAPI()` instance is the documented minimal setup.

## Running it: `fastapi dev` vs `fastapi run`

The `fastapi-cli` tool (installed via the `standard` extra) gives two
relevant commands:

- `fastapi dev main.py` is for local development. It auto-reloads on file
  changes and binds to `127.0.0.1` by default.
- `fastapi run main.py` is for production mode. It has no auto-reload and
  binds to `0.0.0.0` by default. This is what the Docker container runs.

## `async def` vs. plain `def`

`main.py`'s routes are all declared `async def`, but nothing in them
actually awaits anything yet. FastAPI's own docs
spell out exactly how it decides what to do with each route
([fastapi.tiangolo.com/async](https://fastapi.tiangolo.com/async/)):

> "When you declare a path operation function with normal `def` instead of
> `async def`, it is run in an external threadpool that is then awaited,
> instead of being called directly (as it would block the server)."

So a route written as plain `def` doesn't run on the event loop at all.
Starlette silently hands it off to a worker thread pool (the "one thread
per task, OS-managed" model, see [docs/concepts/concurrency-models.md](concurrency-models.md)),
so a slow blocking call inside it can't freeze every other in-flight
request. A route written `async def` runs directly on the event loop,
cooperatively, alongside every other in-flight `async def` route. FastAPI's
own guidance when you're not sure which to use: "If you just don't know,
use normal `def`" (same source). The thread pool is the safe default;
`async def` is the opt-in you reach for once you're actually calling
something `await`-able.

## Path parameters, query parameters, and the request body

FastAPI decides what each of a route function's parameters actually is
purely from how it's declared, not from any special syntax marking it as
one kind or another. Per the official docs
([fastapi.tiangolo.com/tutorial/body](https://fastapi.tiangolo.com/tutorial/body/)):

> "If the parameter is also declared in the path, it will be used as a
> path parameter. If the parameter is of a singular type (like `int`,
> `float`, `str`, `bool`, etc) it will be interpreted as a query
> parameter. If the parameter is declared to be of the type of a Pydantic
> model, it will be interpreted as a request body."

Concretely:

- **Path parameter**: the name appears inside `{curly braces}` in the
  route's path string, like `item_id` in `@app.get("/items/{item_id}")`.
  It's a required part of the URL itself.
- **Query parameter**: a plain parameter (`str`, `int`, etc.) that isn't
  in the path. It comes from `?key=value` in the URL, and it's the kind
  used for things like pagination (`skip`, `limit`).
- **Request body**: a parameter typed as a Pydantic `BaseModel` subclass.
  FastAPI reads it out of the request's JSON body instead of the URL at
  all.

The same detection rule is confirmed from the query-parameter side too
([fastapi.tiangolo.com/tutorial/query-params](https://fastapi.tiangolo.com/tutorial/query-params/)):

> "When you declare other function parameters that are not part of the
> path parameters, they are automatically interpreted as 'query'
> parameters."

So a single route can mix all three freely, FastAPI figures out which is
which parameter-by-parameter, purely from type and from whether the name
matches something in the path.

## `response_model`

`response_model` is a keyword argument on the route decorator itself
(`@app.get("/items", response_model=list[Item])`), separate from the
function's own return type hint. Per the official docs
([fastapi.tiangolo.com/tutorial/response-model](https://fastapi.tiangolo.com/tutorial/response-model/)),
it does four things at once: validates the data being returned, adds a
JSON Schema for it to the OpenAPI docs, serializes it to JSON, and
"limit[s] and filter[s] the output data to what is defined" in the model.

That last point is the real reason it exists as a separate declaration
instead of just relying on the function's return type: the docs give the
exact scenario, wanting to "return a dictionary or a database object, but
declare it as a Pydantic model," so the model does validation and
filtering on data that wasn't already shaped exactly like it. It's also
how you'd deliberately return fewer fields than you have internally, for
example never sending a password hash back out, even if the internal
object has one.

Passing `list[Item]` as a value here (not `list[Item]` as a type
annotation) works because Python classes and generic aliases like
`list[Item]` are ordinary runtime objects, not compile-time-only
constructs. See [python-type-hints.md](python-type-hints.md)'s "Types are runtime values" section for
why that's true in Python but not in TypeScript.

## Dependency injection with `Depends()`

A **dependency** is just a regular function. Wrapping it in `Depends()`
and using it as a parameter's default tells FastAPI to call that function
before running the route, and hand the route whatever it returned. Per
the official docs
([fastapi.tiangolo.com/tutorial/dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)):

> "Whenever a new request arrives, FastAPI will take care of: calling
> your dependency ('dependable') function with the correct parameters,
> get the result from your function, assign that result to the parameter
> in your path operation function."

The key detail that makes this different from just giving a parameter a
plain default value: FastAPI applies the exact same
path-parameter/query-parameter/body detection rules (above) to the
*dependency function's own parameters* too. So a dependency like
`def pagination_params(skip: int = 0, limit: int = 10)` gets its `skip`
and `limit` read from the request's query string, validated and
type-coerced, exactly as if they'd been declared directly on the route.
A plain dict default wouldn't get any of that, it would just be a static
value, not something FastAPI parses out of each incoming request.

The other reason to reach for this over inlining the same parameters on
every route by hand: reuse. The docs frame the whole point as minimizing
repeated logic, useful for "shared logic," "database connections," and
"security, authentication, role requirements," "all these, while
minimizing code repetition." One dependency function, referenced from as
many routes as need the same behavior.

## Custom exception handlers

`@app.exception_handler(SomeExceptionType)` registers a function that
runs whenever `SomeExceptionType` (or a subclass) is raised **anywhere**
in the app, not just in one specific route. FastAPI's own docs are
explicit that this piece of the framework isn't actually FastAPI's own
invention:

> "You can add custom exception handlers with the same exception
> utilities from Starlette." ([fastapi.tiangolo.com/tutorial/handling-errors](https://fastapi.tiangolo.com/tutorial/handling-errors/))

Starlette is the ASGI toolkit FastAPI is built on top of (see "What it
is," above). This is one concrete example of that layering: FastAPI
exposes Starlette's exception-handling mechanism directly, under its own
`@app.exception_handler` decorator, rather than reimplementing it.

A handler receives the incoming `Request` plus the exception instance,
and returns an ordinary response object (commonly a `JSONResponse` from
`fastapi.responses`, see the imports note below). This is the layer above
raising `HTTPException` directly inside a route: it lets route code raise
plain, meaningful Python exceptions (`ItemNotFoundError`, for instance)
and keeps the "turn this into an HTTP status and JSON body" translation
in one central place instead of repeated in every route.

## A note on imports: `fastapi` vs. `fastapi.responses`

`from fastapi import FastAPI, Depends, Request, status` all come from
FastAPI's own top-level package, the "core app-building" surface.
Response classes like `JSONResponse` live in `fastapi.responses` instead,
because they're not FastAPI's own classes at all. Per the docs
([fastapi.tiangolo.com/advanced/custom-response](https://fastapi.tiangolo.com/advanced/custom-response/)):

> "FastAPI provides the same `starlette.responses` as `fastapi.responses`
> just as a convenience for you, the developer. But most of the available
> responses come directly from Starlette."

So `fastapi.responses` is a re-export of Starlette's own response
classes, kept under a `fastapi.*` path purely so you don't need to know
Starlette exists underneath. It's a separate namespace because it's a
separate category of thing, "what you return," not "what you build the
app with."

## What we've built so far

`main.py` now has a `/health` route plus a small in-memory `/items` CRUD
API demonstrating everything above: path parameters (`item_id`), query
parameters via a reusable `Depends()` dependency (`skip`/`limit`),
request bodies (`ItemCreate`), response filtering (`response_model`), and
a custom exception (`ItemNotFoundError`) handled globally instead of
per-route. Still fully synchronous, no real database, on purpose, this is
Phase 2's scope: FastAPI depth before async IO.
