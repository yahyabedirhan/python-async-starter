# Journal

Chronological log of decisions made on this project and why. Book-level
knowledge about the tools involved lives in `docs/concepts/` instead, since
this file is specifically about *this* project's choices.

## 2026-08-17: Project kickoff & scope

Goals for this project: learn FastAPI, learn deploying with Docker to a
Hetzner Cloud VM, learn meaningful asyncio usage. Decided to tackle these as
separate phases instead of mixed together, so each concept can be learned in
isolation:

- **Phase 1**: bare-minimum FastAPI app (`/health` only) deployed to a
  Hetzner VM via Docker, over HTTPS. It's purely operational, with no
  FastAPI depth and no async complexity yet.
- **Phase 2**: FastAPI depth (routing, models, DI, error handling), still
  fully synchronous.
- **Phase 3**: introduce async IO with a concurrent URL-checker feature.
- **Phase 4**: redeploy the fuller app, revisit Docker/Hetzner setup if
  needed.

## 2026-08-17: Phase 1 production-readiness scope

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

## 2026-08-17: HTTPS without a custom domain

Wanted HTTPS but has no domain and doesn't want to buy one just for a demo.
Key fact: Let's Encrypt (the standard free TLS cert issuer) issues certs for
domain names, not bare IPs, so *some* domain is unavoidable for real HTTPS.

Considered:
- Buying a real domain, which is the most "real" option but is unnecessary
  spend for a demo.
- A DuckDNS free subdomain, which requires signup.
- **sslip.io**, a free wildcard DNS service where
  `<ip-with-dashes>.sslip.io` resolves straight to that IP with zero
  signup or config.

Chose **sslip.io**. It's the closest thing to what PaaS platforms like
Vercel give you for free, an instant HTTPS-capable domain, except Hetzner
is IaaS (just a VM + IP, no platform routing layer), so there's no built-in
Hetzner equivalent; sslip.io fills that gap. Will use it with Caddy as the
reverse proxy (Caddy auto-provisions Let's Encrypt certs with minimal
config) once the VM has a static IP.

## 2026-08-17: Project scaffolded with uv + FastAPI

Ran `uv init --python 3.12 --name python-async-starter .`, which pins
Python 3.12 via uv instead of relying on the system's Python 3.9. Then
`uv add "fastapi[standard]"` per FastAPI's own documented recommendation.

`main.py` has a single `/health` route returning `{"status": "ok"}`.
Verified locally with `uv run fastapi run main.py --port 8000` +
`curl http://127.0.0.1:8000/health`. See `docs/concepts/uv.md` and
`docs/concepts/fastapi.md` for the tool-level notes.

## 2026-08-18: commit convention, source citation, and doc style

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

## 2026-08-18: Dockerfile built and tested

Wrote a `Dockerfile` for the app, following the pattern documented in uv's
own Docker guide (`docs.astral.sh/uv/guides/integration/docker`): install
dependencies in one layer before copying the app's code, then install the
project itself in a second layer. This keeps Docker's build cache useful,
since editing `main.py` doesn't force dependencies to reinstall on rebuild.

The container runs as a non-root user (`appuser`, UID/GID 1000, pinned
explicitly rather than left to whatever the system picks), following
Docker's own best-practices page. Reasoning and the exact source are
written up in `docs/concepts/docker.md`, along with a related question that
came up: whether UIDs need to be unique across different projects and
containers on the same machine. They don't, since unlike a network port, a
UID isn't an exclusive, shared resource.

Built the image and ran it locally: `/health` responded correctly, and
`docker exec ... id` confirmed the process really was running as the
unprivileged user, not root.

## 2026-08-18: GitHub repo, README, and progress tracker

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
the repository, so it got changed to a plain list of what's there instead,
and the link to `docs/progress.md` was moved under the Documentation
section where it belongs.

## 2026-08-18: switching to Docker Compose, locally and on Hetzner

Had been running the container directly with `docker build -t ... && docker
run -d -p ...`, retyping the flags each time. Considered switching to
Docker Compose (`docker compose up` / `docker compose down`) instead, and
weighed whether it was worth the extra file.

Landed on: yes, for both local dev and the eventual Hetzner deployment.
Reasoning:

- Locally, it removes the need to remember and retype multi-flag `docker
  run` commands. The tradeoff is close to free, since `docker compose`
  ships as part of Docker itself (no separate install), and the only real
  cost is one more file (`compose.yaml`) that needs to stay in sync with
  the Dockerfile if ports or env vars change.
- On Hetzner, Phase 1's plan already has two containers that need to
  coordinate: the app and Caddy as a reverse proxy in front of it (for
  HTTPS via sslip.io, see the entry above). Compose is a natural fit for
  declaring how multiple containers run together (shared network, restart
  policies) instead of two separate `docker run` invocations kept
  consistent by hand. Redeploying becomes `git pull && docker compose up -d
  --build` rather than a manual stop/rm/run sequence per container.

This changes the plan from "plain `docker run` on the VM" to "Docker
Compose on the VM." Noted here since it affects the deployment steps still
open in `docs/progress.md`.

Added a root-level `compose.yaml` for local dev (single `app` service,
building from the existing `Dockerfile`, port 8000 mapped, `restart:
unless-stopped`). Verified with `docker compose up -d --build`, `curl
http://127.0.0.1:8000/health`, and `docker compose down`. The container and
network both come up and tear down cleanly. The Dockerfile itself didn't
need to change; Compose just orchestrates the image it already builds.

The Hetzner-side `compose.yaml` (adding the Caddy service) is deferred
until the VM step, since Caddy's config depends on having a real IP for
the sslip.io address.

## 2026-08-18: documenting `restart: unless-stopped` instead of dropping it

Question came up: does the local `compose.yaml` actually need `restart:
unless-stopped`, given you start/stop the container yourself during local
dev? The answer is no. It's a no-op locally, since it only matters when
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

## 2026-08-18: Hetzner project + VM created, SSH hardening done

Before touching the console, wrote `docs/concepts/hetzner.md` covering the
account/project relationship and the entities relevant to Phase 1
(Servers, SSH Keys, Firewalls, API Tokens), sourced from Hetzner's own
docs. Also did a plain-language recap of how SSH key pairs work
(private key never leaves your machine, public key is what gets uploaded)
and of inbound vs. outbound traffic, since both were being used
"blindly" otherwise.

**What got created**: one Hetzner project and one server. The server is
`ubuntu-4gb-fsn1-1`, which is Hetzner's auto-generated name describing it
as an Ubuntu box with 4GB of RAM in the Falkenstein datacenter. It runs
Ubuntu 26.04, with 2 vCPU, 4GB RAM, 40GB SSD, x86 (Intel, not ARM64),
public IPv4 and IPv6, and no private network. It costs $7 a month.

**Deliberately left unset** at creation time, each for a specific reason:
- **Backups**, since it's extra cost and already listed as an explicitly
  deferred gap for Phase 1 in this journal's "production-readiness scope"
  entry.
- **Placement Group**, which is only useful for spreading *multiple*
  servers across physical hardware for failure isolation, and is
  meaningless with one server.
- **Labels**, which are organizational and filtering metadata, not needed
  yet with a single server and (soon) a single firewall.
- **Cloud-init / cloud config** could have scripted the whole hardening
  step below automatically on first boot, but that was skipped on
  purpose. The point of doing this walkthrough by hand once is to
  actually understand each step, not have it happen invisibly. Worth
  revisiting for automation once these steps are already understood
  (maybe Phase 4).

One firewall-related sequencing question came up: unlike SSH keys
(which must be attached at server-creation time and can't be added after
via the console), Hetzner Cloud Firewalls can be attached to a server at
any point after it's created. So the plan is to create the VM first and
attach a firewall separately, not block VM creation on having a firewall
ready.

**SSH hardening, done directly on the VM** (see
`docs/concepts/hetzner.md` for why each piece matters):
1. Connected as `root` first (the only user Hetzner's base Ubuntu image
   has), confirmed key-based login worked with no password prompt.
2. Created a non-root user with `adduser`, added it to the `sudo` group.
3. Copied `root`'s `authorized_keys` file into the new user's `~/.ssh/`,
   fixed ownership (`chown`) and permissions (`chmod 700` on the
   directory, `600` on the file, since SSH silently refuses
   overly-permissive key files).
4. Verified the new user could log in via SSH (key-based, no password)
   and that `sudo whoami` worked (prompts for the account's local
   password, separate from SSH auth entirely).
5. Edited `/etc/ssh/sshd_config`: `PermitRootLogin no`,
   `PasswordAuthentication no`. Restarted `sshd`.
6. Verified, with the original root session kept open as a safety net
   until confirmed: the non-root user can still log in, and `ssh root@<ip>`
   is now refused outright.

Next: create the Hetzner Cloud Firewall (22 + app port only, matching the
"only 22 and the app port open" scope decided earlier), attach it to the
VM, then install Docker + Compose there and deploy.

## 2026-08-18: firewall, Docker install, and first deploy to the VM

**Firewall**: created in the console, inbound rules for TCP 22 (SSH) and
TCP 8000 (the app's port, matching `EXPOSE 8000`/`compose.yaml`, and will
swap for 80/443 once Caddy is added), inbound ICMP also allowed so `ping`
works. The diagnostic convenience outweighs the minor scan-resistance
lost by allowing it. Outbound left at its default (allowed). Attached
directly to the server.

**Docker + Compose install**: followed Docker's official Ubuntu install
guide
([docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/)).
Added Docker's APT repository and GPG key, then installed
`docker-ce docker-ce-cli containerd.io docker-buildx-plugin
docker-compose-plugin`. Added the non-root user to the `docker` group
(`usermod -aG docker $USER`) so Docker commands don't need `sudo`, the
same idea as the earlier `sudo` group addition. Installed versions: Docker
29.7.2, Compose 5.5.0.

One snag: ran a Docker command in the same SSH session the `usermod` was
run in, and got "permission denied ... docker.sock". Group membership
changes don't apply to an already-open session, only new ones. Fixed by
disconnecting and reconnecting over SSH.

**First deploy**: cloned the public GitHub repo directly onto the VM
(`git clone https://github.com/yahyabedirhan/python-async-starter.git`),
then ran the exact same `docker compose up -d --build` already used
locally. No VM-specific compose file was needed yet, since Caddy (the only
planned VM-specific addition) isn't in the picture until the HTTPS step.

**Verified end to end**: `curl http://127.0.0.1:8000/health` from inside
the VM, and `curl http://167.233.107.219:8000/health` from a laptop
outside the VM, both returned `{"status":"ok"}`. The external check is
the one that actually proves the whole chain: Docker Compose running the
container correctly, the container's port reaching the host, and the
Hetzner firewall rule correctly allowing port 8000 in.

Remaining for Phase 1: add Caddy as a second service in a VM-specific
`compose.yaml`, and point a sslip.io address at the VM to get HTTPS
working end-to-end.

## 2026-08-18: Caddy + sslip.io: HTTPS working, Phase 1 complete

Before touching config, wrote three concept docs: `docs/concepts/caddy.md`
and `docs/concepts/sslip-io.md` (tool-specific, sourced from their own
official docs), plus `docs/concepts/https-fundamentals.md`, a broader
write-up of the actual problem space (naming vs. trust/encryption, SSL
vs. TLS, DV/OV/EV, ACME, the traditional manual cert workflow, and
alternatives at each layer), since the three tools together were
initially confusing as a pile of unrelated names.

While writing those, corrected a structural mistake: the concept docs had
started referencing `docs/progress.md` / `docs/journal.md` and specific
phase numbers, creating a two-way dependency between the concept docs and
the phase-tracking docs. Fixed by stripping all such references back out.
Concept docs should only ever be pointed *into* from phase docs, never
the other way around, so they stay reusable on their own.

**Implementation**: rather than editing the existing `compose.yaml`
directly, added a separate `compose.prod.yaml` override file. Caddy only
makes sense once a real domain exists (the VM's sslip.io hostname), so it
has no reason to touch local dev. `compose.prod.yaml` adds a `caddy`
service (official `caddy:2` image, ports 80/443 + 443/udp for HTTP/3, a
mounted `Caddyfile`, and two named volumes, `caddy_data` for the
certificate itself and `caddy_config` for Caddy's runtime state, both
needing to persist across restarts so Caddy doesn't re-request a
certificate every time the container recreates), and clears the `app`
service's direct `8000:8000` port publish (`ports: []`), since nothing
external should reach the app directly anymore, only through Caddy.

`Caddyfile` is a single site block. `167-233-107-219.sslip.io` (the
project's VM IP with dots swapped for hyphens, per sslip.io's own
convention) is reverse-proxied to `app:8000`, and `app` resolves via
Compose's own internal DNS, so no hardcoded container IP is needed.

**Firewall**: updated in the console. Removed the TCP 8000 rule (no
longer needed, nothing external hits the app port directly now), added
TCP 80 and TCP 443. 22 and ICMP unchanged.

**Deploy**: committed and pushed the new files, `git pull`ed on the VM,
then brought it up with both compose files merged:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d --build
```

Caddy obtained a certificate from Let's Encrypt automatically on startup.
No manual ACME steps, no certbot, nothing beyond having the domain in
the `Caddyfile` and ports 80/443 reachable.

**Verified**: `curl https://167-233-107-219.sslip.io/health` returns
`{"status":"ok"}` over real, browser-trusted HTTPS, with no port needed in
the URL (443 is HTTPS's implicit default) and no certificate warnings.

**Phase 1 is done.** FastAPI app, containerized, deployed to a hardened
Hetzner VM, reachable over real HTTPS with a free automatically-renewing
certificate. No domain purchase, no manual cert management. Next up per
`docs/progress.md`: Phase 2, FastAPI depth (routing, request/response
models, dependency injection, error handling), still fully synchronous.
