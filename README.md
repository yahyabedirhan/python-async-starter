# python-async-starter

A project demonstrating FastAPI and asyncio with a realistic example. It's
meant to be containerized with Docker and deployed to a Hetzner Cloud VM
over HTTPS.

## Content

- A **FastAPI** app.
- A **Dockerfile** to containerize it.
- An **asyncio**-based feature for concurrent HTTP handling.
- Deployment setup for a **Hetzner Cloud VM**, served over HTTPS.

## Documentation

- [`docs/progress.md`](docs/progress.md) — current status of the project.
- [`docs/journal.md`](docs/journal.md) — a running log of decisions made on
  this project, and why.
- [`docs/concepts/`](docs/concepts) — short, plain-language explainers for
  each tool used (uv, FastAPI, Docker, ...).

## Running locally

```bash
uv run fastapi dev main.py
```

Then visit `http://127.0.0.1:8000/health`.
