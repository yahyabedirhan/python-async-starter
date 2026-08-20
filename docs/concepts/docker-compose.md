# Docker Compose

## What it is

Docker Compose is a layer on top of plain Docker, not a replacement for it.
It doesn't change how images are built or how containers run underneath.
The same Docker engine, images, and containers are still there. What it
changes is how you describe and start them: instead of typing a `docker
run` command with a long list of flags (ports, restart policy, network),
you write those settings once in a file called `compose.yaml`, and run
`docker compose up` / `docker compose down` instead.

It ships as part of Docker itself on any reasonably current install (this
is general knowledge, not from a fetched source), so there's no separate
tool to install.

## What's in this project's `compose.yaml`

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
```

- **`services`**: the list of containers Compose manages. Right now there's
  just one, called `app`.
- **`build: .`**: build the image from the `Dockerfile` in this directory,
  the same one used for plain `docker build`.
- **`ports`**: maps port 8000 on the host machine to port 8000 inside the
  container, equivalent to `docker run`'s `-p 8000:8000`.
- **`restart: unless-stopped`**: what Docker does if the container's
  process dies or the Docker daemon itself restarts (e.g. the machine
  reboots).
  - If the container **crashes** (the app exits with an error), Docker
    restarts it automatically.
  - If you **stop it on purpose** (`docker compose down`, or `docker
    stop`), Docker respects that and leaves it stopped. It won't fight
    you and bring it back. That's the "unless-stopped" part: keep
    restarting it, *unless* a human explicitly stopped it.
  - If the **whole machine reboots**, Docker restarts the container when
    it comes back up (as long as it wasn't in a manually-stopped state),
    so the app returns without anyone having to SSH in.

    There's a similar policy, `restart: always`, which restarts the
    container even after a manual stop once the machine reboots.
    `unless-stopped` is generally preferred because it respects your last
    manual action.

  This only matters when something other than you needs to bring the
  container back, whether that's a crash or a reboot on a server nobody's
  watching. For
  local dev, where you start/stop it yourself, it's a no-op: it's worth
  keeping anyway, so a local file and a server-side file don't diverge on
  a setting that matters once there's a real server involved.

## The commands

```bash
docker compose up -d --build   # build (if needed) and start, in the background
docker compose down            # stop and remove the container + network
```

`docker compose up` without `-d` runs in the foreground and streams logs to
your terminal, which is useful while debugging. `-d` ("detached") runs it
in the background instead, closer to how it'd run unattended on a server.

## Why use it over plain `docker run`

Two situations where it earns its keep:

1. **A single container, run repeatedly**: it replaces retyping multi-flag
   `docker run` commands with two short ones. The Dockerfile doesn't
   change at all; Compose just orchestrates the same image it already
   builds.
2. **Multiple containers that need to coordinate**, for example an app
   plus a reverse proxy in front of it. Compose is a better fit than several
   independent `docker run` commands for declaring how multiple containers
   run together (shared network, restart policies), and makes redeploys a
   single command (`docker compose up -d --build`) instead of a manual
   per-container stop/rm/run sequence.

## One thing that doesn't change

Secrets and environment-specific values (an API key, a domain name, a TLS
contact email) still shouldn't be hardcoded into the committed
`compose.yaml`. Those belong in an untracked `.env` file or an
environment-specific override, both of which Compose supports, the same
way they'd be kept out of a plain `docker run` command.
