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

## What we've built so far

`main.py` has one `FastAPI()` instance and one route:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

Deliberately nothing else yet: no models, no dependency injection, and no
error handling. Just enough to prove the operational path: code ->
container -> reachable server.
