# Progress tracker

A simple checklist of what's done and what's left. For the reasoning behind
decisions, see `docs/journal.md`. For tool-specific explanations, see
`docs/concepts/`.

## Phase 1 — operational foundation (FastAPI + Docker + Hetzner, plain HTTPS)

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
- [ ] Create the Hetzner Cloud VM (guided walkthrough)
- [ ] Harden the VM: SSH key-only login, non-root user, Hetzner Cloud Firewall
- [ ] Install Docker + Docker Compose on the VM and deploy via `docker compose up -d` (restart policy)
- [ ] Verify the app is reachable from outside over the VM's IP
- [ ] Add Caddy as a reverse proxy in front of the app, as a second service in the VM's `compose.yaml`
- [ ] Point a sslip.io address at the VM and confirm HTTPS works end-to-end

## Phase 2 — FastAPI depth (not started)

Routing, request/response models, dependency injection, error handling.
Still fully synchronous — no async concepts introduced yet.

## Phase 3 — async IO (not started)

Introduce the concurrent URL-checker feature using `asyncio.gather` +
`httpx.AsyncClient`. Compare against a sequential version to make the
speedup visible.

## Phase 4 — redeploy + CI/CD (not started)

Redeploy the fuller app. Add a GitHub Actions workflow to auto-deploy on
push to `main`. Revisit Docker/Hetzner setup if needed at that point.
