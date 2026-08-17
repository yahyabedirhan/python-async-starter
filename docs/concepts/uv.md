# uv

## What it is

`uv` is a Python package and project manager, written in Rust. It replaces the
usual combo of `pip` + `venv` + `pip-tools` (and often `pyenv`) with one fast
tool. It manages:

- Python interpreter versions (downloads and pins one per project)
- A project's virtual environment (`.venv/`)
- Dependencies, recorded in `pyproject.toml` and locked in `uv.lock`

## Key files it creates/manages

- `pyproject.toml` — project metadata and dependency list
- `uv.lock` — exact resolved versions, committed to git for reproducibility
- `.python-version` — pins which Python version the project uses
- `.venv/` — the actual virtual environment (not committed)

## Core commands used so far

| Command | What it does |
|---|---|
| `uv init --python 3.12 --name <name> .` | Scaffold a new project in the current directory |
| `uv add <package>` | Add a dependency, update `pyproject.toml` + `uv.lock`, install it |
| `uv run <command>` | Run a command inside the project's managed virtual environment (creates it if missing) |
| `uv sync` | Make `.venv` match `pyproject.toml`/`uv.lock` exactly (install missing, remove extraneous) |

## `uv sync` — deterministic environment installs

`uv sync` doesn't add or resolve anything new — it makes `.venv` match
`pyproject.toml`/`uv.lock` exactly, installing what's missing and removing
what shouldn't be there. npm comparison: it's `npm ci`, not `npm install` —
the lockfile is the source of truth, not something to be updated.

Where it fits with the commands above: `uv add` and `uv run` both call
`sync` internally when needed (after adding a dependency, or before running
if the lockfile changed) — `uv sync` is just the explicit, standalone form,
useful when you want the environment updated without also running a
command (e.g. in a Dockerfile, or after pulling someone else's lockfile
changes).

Flags used in this project's Dockerfile:

- **`--locked`** — fail instead of silently re-resolving if `uv.lock` is
  out of sync with `pyproject.toml`. A build should fail loudly rather than
  drift to different dependency versions than what's committed.
- **`--no-install-project`** — install only the dependencies, skip
  installing our own code as a package. Used for Docker layer caching: sync
  once with just `pyproject.toml`/`uv.lock` copied in (cached unless
  dependencies change), then copy the actual source and `sync` again
  (without the flag) to install the project itself.

## Running things: always `uv run`

`uv run <command>` executes inside the project's `.venv` — the pinned Python
version, with all `uv add`ed dependencies available — without manually
activating anything. Examples used in this project:

| Goal | Command |
|---|---|
| Plain script | `uv run python script.py` |
| Dev server (auto-reload) | `uv run fastapi dev main.py` |
| Prod server (what Docker runs) | `uv run fastapi run main.py` |
| REPL with deps available | `uv run python` |

It also auto-syncs the environment first if `pyproject.toml`/`uv.lock`
changed since the last run, so you can't accidentally run against a stale
environment — this is why `uv run` is preferred over manually
`source .venv/bin/activate`-ing.

## `uv run fastapi dev` — how it resolves (npm comparison)

If you're coming from npm, `uv run <cli>` maps to `npx <cli>`, **not** to
`npm run <script>`:

- `npm run test` works because *you* defined a `"scripts": {"test": ...}`
  entry in your own `package.json`. There's no equivalent custom entry for
  `fastapi` in our `pyproject.toml` — we never defined it.
- Instead, the **`fastapi` package itself** declares, in its own packaging
  metadata (`[console_scripts]`, the Python-packaging equivalent of a
  library's `"bin"` field in *its* `package.json` — e.g. how ESLint ships an
  `eslint` binary), that it provides a command:
  ```
  fastapi = fastapi.cli:main
  ```
- When you install it (`uv add "fastapi[standard]"`), the installer
  generates a real executable at `.venv/bin/fastapi` — same idea as npm
  generating `node_modules/.bin/eslint` on install.
- `uv run fastapi dev main.py` puts `.venv/bin` on `PATH` for that one
  command and runs it — functionally `npx fastapi dev main.py`.
- `dev` isn't a separate script — it's just an argument the `fastapi`
  program parses internally (built with a CLI library called Typer), same
  as `git branch` (`branch` is an arg `git` parses) or `eslint --fix`.

Docs: subcommands (`dev`/`run`/`deploy`) at
[fastapi.tiangolo.com/fastapi-cli](https://fastapi.tiangolo.com/fastapi-cli/);
the entry-point declaration itself lives in FastAPI's own `pyproject.toml`
under `[project.scripts]` — Python's equivalent of npm's `"bin"` field.

Note: Python packaging *does* have an equivalent of npm's `"scripts"` table
too — `[project.scripts]` in our **own** `pyproject.toml` — but that's for
exposing installable commands from a package we publish, not arbitrary task
shortcuts. For npm-style ad-hoc task running, Python projects typically
reach for a separate tool (e.g. `just`, `invoke`) — not something `uv`
provides natively, and not something we need here.

## Project Python vs. system Python

These are two separate things:

- **System `python3`** (what `python3 --version` shows in your shell) — on
  macOS this is Apple's own bundled Python, shared machine-wide.
  Independent of any project.
- **Project Python** — `uv` downloads and manages its own interpreters
  (in `~/.local/share/uv/python/...`), pinned per-project via
  `.python-version` / `requires-python` in `pyproject.toml`. `uv run` always
  uses this one, never the system one.

This project pins **3.12** even though the system Python is 3.9.6. Reasons:
3.9 is close to end-of-life (security support ends Oct 2025), and FastAPI's
tooling assumes a current Python. Since `uv` manages its own interpreter
entirely separately from the system one, there's no need to touch or
upgrade the system Python at all — `uv init --python 3.12` downloads an
isolated 3.12 with no side effects outside the project.

**Should you upgrade your system Python to match?** Generally, no — leave
it alone. macOS tooling sometimes relies on the specific bundled Python, so
replacing it is a common way to break unrelated things for no benefit: every
project's actual Python is decided by its own `uv`/`.python-version` pin,
not by the system default.
