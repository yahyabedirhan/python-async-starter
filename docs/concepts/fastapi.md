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

No special folder structure is required for a small project — a single
`main.py` with an `app = FastAPI()` instance is the documented minimal setup.

## Running it: `fastapi dev` vs `fastapi run`

The `fastapi-cli` tool (installed via the `standard` extra) gives two
relevant commands:

- `fastapi dev main.py` — local development: auto-reload on file changes,
  binds to `127.0.0.1` by default.
- `fastapi run main.py` — production mode: no auto-reload, binds to
  `0.0.0.0` by default. This is what the Docker container runs.

## What we've built so far

`main.py` — one `FastAPI()` instance, one route:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

Deliberately nothing else yet — no models, no dependency injection, no
error handling. Just enough to prove the operational path: code ->
container -> reachable server.
