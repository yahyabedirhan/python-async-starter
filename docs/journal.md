# Journal

Chronological log of decisions made on this project and why. Book-level
knowledge about the tools involved lives in `docs/concepts/` instead — this
file is specifically about *this* project's choices.

## 2026-08-17 — Project kickoff & scope

Goals for this project: learn FastAPI, learn deploying with Docker to a
Hetzner Cloud VM, learn meaningful asyncio usage. Decided to tackle these as
separate phases instead of mixed together, so each concept can be learned in
isolation:

- **Phase 1**: bare-minimum FastAPI app (`/health` only) deployed to a
  Hetzner VM via Docker, over HTTPS. Purely operational — no FastAPI depth,
  no async complexity yet.
- **Phase 2**: FastAPI depth (routing, models, DI, error handling) — still
  synchronous.
- **Phase 3**: introduce async IO with a concurrent URL-checker feature.
- **Phase 4**: redeploy the fuller app, revisit Docker/Hetzner setup if
  needed.

## 2026-08-17 — Phase 1 production-readiness scope

Considered the usual "production readiness" checklist (reverse proxy, TLS,
firewall, SSH hardening, non-root users, restart policies, monitoring,
backups, CI/CD) and decided what's in vs. out of scope for a learning demo:

**In scope for Phase 1:**
- SSH key-only auth, non-root user on the VM
- Hetzner Cloud Firewall (only 22 and the app port open)
- Docker with a restart policy, non-root user inside the container
- HTTPS via a reverse proxy (see below)

**Explicitly deferred** (noted as known gaps, not implemented):
- Automatic OS security updates
- VM snapshots/backups
- CI/CD pipeline
- Centralized logging/monitoring beyond a basic health check

## 2026-08-17 — HTTPS without a custom domain

Wanted HTTPS but has no domain and doesn't want to buy one just for a demo.
Key fact: Let's Encrypt (the standard free TLS cert issuer) issues certs for
domain names, not bare IPs — so *some* domain is unavoidable for real HTTPS.

Considered:
- Buying a real domain — most "real," but unnecessary spend for a demo
- DuckDNS free subdomain — requires signup
- **sslip.io** — free wildcard DNS service, `<ip-with-dashes>.sslip.io`
  resolves straight to that IP with zero signup or config

Chose **sslip.io**. It's the closest thing to what PaaS platforms like
Vercel give you for free (an instant HTTPS-capable domain) — except Hetzner
is IaaS (just a VM + IP, no platform routing layer), so there's no built-in
Hetzner equivalent; sslip.io fills that gap. Will use it with Caddy as the
reverse proxy (Caddy auto-provisions Let's Encrypt certs with minimal
config) once the VM has a static IP.

## 2026-08-17 — Project scaffolded with uv + FastAPI

Ran `uv init --python 3.12 --name python-async-starter .` — pins Python 3.12
via uv instead of relying on the system's Python 3.9. Then
`uv add "fastapi[standard]"` per FastAPI's own documented recommendation.

`main.py` has a single `/health` route returning `{"status": "ok"}`.
Verified locally with `uv run fastapi run main.py --port 8000` +
`curl http://127.0.0.1:8000/health`. See `docs/concepts/uv.md` and
`docs/concepts/fastapi.md` for the tool-level notes.

## 2026-08-18 — commit convention, source citation, doc style

Set up `AGENTS.md` (with a `CLAUDE.md` symlink pointing to it) as a place
for standing rules about how work on this project should be done. Three
rules went in today:

- **Commit messages** follow Conventional Commits prefixes (`feat:`,
  `fix:`, etc.), a 50-character subject line, always lowercase (even for
  names like "fastapi"), and optional dash-bulleted detail lines below a
  blank line.
- **Cite external sources.** Any time a recommendation comes from an
  official doc, a blog post, or a tool like Context7, say so and link it,
  so it can be checked or revisited later. If something instead comes from
  general knowledge rather than a fetched source, say that too.
- **Documentation style.** Write `docs/` content in plain, natural
  sentences, like explaining something out loud to a person, not
  compressed notes. Should be understandable even half-asleep.

The citation rule came out of a real moment: a Dockerfile pattern was
written without saying where it came from, and asking about it led to
finding the actual source (uv's own Docker guide) after the fact instead of
during. Better to cite as we go.

## 2026-08-18 — Dockerfile built and tested

Wrote a `Dockerfile` for the app, following the pattern documented in uv's
own Docker guide (`docs.astral.sh/uv/guides/integration/docker`): install
dependencies in one layer before copying the app's code, then install the
project itself in a second layer. This keeps Docker's build cache useful —
editing `main.py` doesn't force dependencies to reinstall on rebuild.

The container runs as a non-root user (`appuser`, UID/GID 1000, pinned
explicitly rather than left to whatever the system picks), following
Docker's own best-practices page. Reasoning and the exact source are
written up in `docs/concepts/docker.md`, along with a related question that
came up: whether UIDs need to be unique across different projects/
containers on the same machine (they don't — unlike a network port, a UID
isn't an exclusive, shared resource).

Built the image and ran it locally: `/health` responded correctly, and
`docker exec ... id` confirmed the process really was running as the
unprivileged user, not root.

## 2026-08-18 — GitHub repo, README, progress tracker

Created `docs/progress.md` as a plain checklist of what's done and what's
left, separate from this journal (which is about *why*, not a status
board). Phase 1 is tracked item-by-item; later phases are just short
summaries for now.

Created a public GitHub repository (`yahyabedirhan/python-async-starter`)
and pushed the `main` branch to it.

Wrote a short `README.md` for anyone landing on the repo for the first
time. Went through a few rounds of trimming: the first sentence originally
led with "this is a learning project," which got dropped in favor of just
describing what the project demonstrates (FastAPI and asyncio) and what
it's deployed with (Docker, Hetzner). The section listing the project's
pieces was originally written as a phase-by-phase build sequence, which
reads more like a progress report than a description of what's actually in
the repository — changed it to a plain list of what's there instead, and
moved the link to `docs/progress.md` under the Documentation section where
it belongs.

## 2026-08-18 — switching to Docker Compose, locally and on Hetzner

Had been running the container directly with `docker build -t ... && docker
run -d -p ...`, retyping the flags each time. Considered switching to
Docker Compose (`docker compose up` / `docker compose down`) instead, and
weighed whether it was worth the extra file.

Landed on: yes, for both local dev and the eventual Hetzner deployment.
Reasoning:

- Locally, it removes the need to remember/retype multi-flag `docker run`
  commands — the tradeoff is close to free, since `docker compose` ships as
  part of Docker itself (no separate install), and the only real cost is
  one more file (`compose.yaml`) that needs to stay in sync with the
  Dockerfile if ports or env vars change.
- On Hetzner, Phase 1's plan already has two containers that need to
  coordinate: the app and Caddy as a reverse proxy in front of it (for
  HTTPS via sslip.io — see the entry above). Compose is a natural fit for
  declaring how multiple containers run together (shared network, restart
  policies) instead of two separate `docker run` invocations kept
  consistent by hand. Redeploying becomes `git pull && docker compose up -d
  --build` rather than a manual stop/rm/run sequence per container.

This changes the plan from "plain `docker run` on the VM" to "Docker
Compose on the VM" — noted here since it affects the deployment steps still
open in `docs/progress.md`.

Added a root-level `compose.yaml` for local dev (single `app` service,
building from the existing `Dockerfile`, port 8000 mapped, `restart:
unless-stopped`). Verified with `docker compose up -d --build`, `curl
http://127.0.0.1:8000/health`, and `docker compose down` — container and
network both come up and tear down cleanly. The Dockerfile itself didn't
need to change; Compose just orchestrates the image it already builds.

The Hetzner-side `compose.yaml` (adding the Caddy service) is deferred
until the VM step, since Caddy's config depends on having a real IP for
the sslip.io address.

## 2026-08-18 — documenting `restart: unless-stopped` instead of dropping it

Question came up: does the local `compose.yaml` actually need `restart:
unless-stopped`, given you start/stop the container yourself during local
dev? Answer is no — it's a no-op locally, since it only matters when
something other than you needs to bring the container back (a crash, or a
machine reboot on a server nobody's watching).

Considered removing it from the local file for that reason, but decided to
keep it instead: the standing rule here is not to have unexplained config
sitting in the codebase, so rather than drop it, added a short comment in
`compose.yaml` pointing at the reasoning, plus the full explanation
(including the crash/manual-stop/reboot distinction, and `unless-stopped`
vs `always`) in `docs/concepts/docker-compose.md`. Keeping it also means
the local file's shape matches what the Hetzner `compose.yaml` will need,
instead of the two diverging on a setting that does matter there.
