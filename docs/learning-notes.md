# Learning notes

Personal notes on things learned during this project, written day by day.
This is different from `docs/journal.md` (which tracks project decisions)
and `docs/concepts/` (which are reference explainers) — this file is about
what actually stuck, in your own words, including things still worth
revisiting.

## 2026-08-18

- The most basic FastAPI project just needs `from fastapi import FastAPI`,
  an `app = FastAPI()` instance, and a function decorated with something
  like `@app.get("/health")`. No boilerplate beyond that.

- `uv run <command>` runs a command using the project's own virtual
  environment: the pinned Python version, with all the installed packages
  available.

- `uv sync` makes the virtual environment match what's listed in
  `pyproject.toml` and `uv.lock`. It's closer to `npm ci` than
  `npm install` — it doesn't add new packages or update the lockfile on its
  own, it just reproduces exactly what the lockfile already says.

- The `--locked` flag on `uv sync` makes it fail loudly if `uv.lock` is out
  of sync with `pyproject.toml`, instead of quietly re-resolving versions.

- The `--no-install-project` flag on `uv sync` means "install the
  dependencies, but don't install our own code as a package." It's a scope
  limiter on what gets installed.

- **Still to revisit**: why the Dockerfile runs `uv sync` twice (once with
  `--no-install-project` before copying the code, once without it after).
  The short version is that it's about Docker's layer caching — splitting
  it in two means editing application code doesn't force all dependencies
  to reinstall on every rebuild — but this hasn't fully clicked yet and is
  worth coming back to, ideally by watching a rebuild happen after a code
  change and seeing which layers get skipped.
