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
