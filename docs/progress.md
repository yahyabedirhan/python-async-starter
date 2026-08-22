# Progress tracker

A simple checklist of what's done and what's left. For the reasoning behind
decisions, see `docs/journal.md`. For tool-specific explanations, see
`docs/concepts/`.

## Phase 1: operational foundation (FastAPI + Docker + Hetzner, plain HTTPS)

- [x] Git repo initialized
- [x] Decided the four-phase plan (this file's structure)
- [x] Decided Phase 1 production-readiness scope (what's in/out for a learning demo)
- [x] Decided HTTPS approach: Caddy reverse proxy + free sslip.io domain (no domain purchase needed)
- [x] Project scaffolded with `uv`, pinned to Python 3.12
- [x] FastAPI app created with a single `/health` endpoint, tested locally
- [x] `AGENTS.md` written: commit message convention, source-citation rule, documentation style rule (+ `CLAUDE.md` symlink)
- [x] First commit made
- [x] Dockerfile written: multi-layer `uv sync` caching, non-root user with pinned UID/GID
- [x] Docker image built and tested locally (`/health` reachable, confirmed running as non-root)
- [x] `docs/concepts/uv.md`, `docs/concepts/fastapi.md`, `docs/concepts/docker.md` written
- [x] Decided to use Docker Compose instead of raw `docker run`, for local dev and the Hetzner deployment
- [x] `compose.yaml` added for local dev (single `app` service), tested with `docker compose up`/`down`
- [x] `docs/concepts/docker-compose.md` written
- [x] `docs/concepts/hetzner.md` written (projects, servers, SSH keys, firewalls, API tokens)
- [x] Hetzner project + VM created (`ubuntu-4gb-fsn1-1`, Ubuntu 26.04, 2 vCPU / 4GB / 40GB, Falkenstein, x86)
- [x] SSH key uploaded at creation, confirmed key-based login as `root` works
- [x] Non-root sudo user created, SSH key copied over, confirmed login + `sudo` both work
- [x] Root SSH login and password authentication disabled (`sshd_config`), confirmed root login is now refused
- [x] Create the Hetzner Cloud Firewall (22 + app port only) and attach it to the VM
- [x] Install Docker + Docker Compose on the VM and deploy via `docker compose up -d` (restart policy)
- [x] Verify the app is reachable from outside over the VM's IP
- [x] Add Caddy as a reverse proxy in front of the app, as a second service in the VM's `compose.yaml`
- [x] Point a sslip.io address at the VM and confirm HTTPS works end-to-end

Phase 1 complete: `https://167-233-107-219.sslip.io/health` returns
`{"status":"ok"}` over real, trusted HTTPS.

## Phase 2: FastAPI depth

- [x] Routing with path parameters (`/items/{item_id}`) and query parameters (`skip`/`limit`)
- [x] Request/response models with Pydantic (`ItemCreate`, `Item`, `response_model`)
- [x] Dependency injection with `Depends()` (reusable pagination params)
- [x] Error handling with a custom exception + global `@app.exception_handler`
- [x] `/items` CRUD (`POST`, `GET` list + detail, `PUT`, `DELETE`) implemented and tested end to end
- [x] `docs/concepts/fastapi.md`, `docs/concepts/pydantic.md`, `docs/concepts/python-type-hints.md` updated; `docs/concepts/python-objects-and-dicts.md` added

Phase 2 complete: still fully synchronous, no async concepts introduced yet,
that's Phase 3's job.

## Phase 3: async IO (not started)

Introduce the concurrent URL-checker feature using `asyncio.gather` +
`httpx.AsyncClient`. Compare against a sequential version to make the
speedup visible.

## Phase 4: redeploy + CI/CD (not started)

Redeploy the fuller app. Add a GitHub Actions workflow to auto-deploy on
push to `main`. Revisit Docker/Hetzner setup if needed at that point.
