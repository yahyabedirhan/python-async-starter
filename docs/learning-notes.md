# Learning notes

Personal notes on things learned during this project, written day by day.
This is different from `docs/journal.md` (which tracks project decisions)
and `docs/concepts/` (which are reference explainers) — this file is about
what actually stuck, in your own words, including things still worth
revisiting.

## 2026-08-18

### uv

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

### FastAPI

- The most basic FastAPI project just needs `from fastapi import FastAPI`,
  an `app = FastAPI()` instance, and a function decorated with something
  like `@app.get("/health")`. No boilerplate beyond that.

### Docker & Docker Compose

- **Still to revisit**: why the Dockerfile runs `uv sync` twice (once with
  `--no-install-project` before copying the code, once without it after).
  The short version is that it's about Docker's layer caching — splitting
  it in two means editing application code doesn't force all dependencies
  to reinstall on every rebuild — but this hasn't fully clicked yet and is
  worth coming back to, ideally by watching a rebuild happen after a code
  change and seeing which layers get skipped.

- **Docker Compose vs. plain `docker` commands**: Compose doesn't change
  how images are built or containers run underneath — same Docker engine,
  same containers. It just lets the config (ports, restart policy, build
  context) live in one `compose.yaml` file instead of being retyped as
  flags every time. `docker compose up -d --build` / `docker compose down`
  replace the old `docker build -t ... && docker run -d -p ...` combo.

- **`restart: unless-stopped`**: needed so the container comes back
  automatically if it crashes, or if the whole machine reboots (relevant
  on the Hetzner VM, since nobody's sitting there to restart it manually).
  It won't fight you if you stopped the container on purpose — that's the
  "unless-stopped" part.

### Hetzner

- **Firewalls**: attached to a server, filter inbound traffic. Inbound is
  blocked by default unless a rule allows it; outbound is allowed by
  default. For this project, the rule opens TCP **22** (SSH) and TCP
  **8000** (the app's port) — not "TCP 12," 22 is the standard port SSH
  listens on.

- **Rescaling**: Hetzner supports resizing a server's vCPU/RAM after
  creation — no need to destroy and recreate a server to change its size.
  The server has to be powered off first, so there's a short downtime
  window during the resize. Disk size is a bit asymmetric: it stays the
  same by default when rescaling, and there's an option to grow it to
  match the new plan, but doing that permanently blocks downgrading to a
  smaller plan afterward.

### SSH, Linux users, and permissions

- **SSH keys are an asymmetric key pair**: a private key that never
  leaves your machine, and a public key that's safe to hand out (to
  GitHub, to Hetzner, to a server). The server can verify you hold the
  matching private key without the private key ever being transmitted.
  "SSH key" is really just this same public/private key idea — the same
  pattern shows up as TLS certificates, GPG keys, and JWT signing,
  just applied to different problems.

- **Root vs. a non-root user with `sudo`**: `sudo` gives a normal user
  temporary root access, one command at a time, instead of that user
  having full power all the time by default. This is also why we blocked
  SSH login for `root` and only allowed it for our own user: `root` is a
  username every Linux server has, so it's an easy target to
  brute-force. Our own username isn't guessable the same way, so it's
  harder to attack even before factoring in that SSH needs the right key
  too.

- **`sudoers` and the `sudo` group**: `sudoers` is the file that decides
  who's allowed to use `sudo`. The `sudo` group is the default group
  inside that file that's already trusted with full access. Running
  `usermod -aG sudo yourname` just adds our user to that group — it
  doesn't change the `sudoers` file itself, it just puts our user into
  the group the file already trusts.

- **`chmod 700` vs. `chmod 600`, and why execute means different things
  on a directory vs. a file**: on the `.ssh` **directory**, `700` gives
  the owner read (list what's inside), write (create/delete files in it),
  and execute — and on a directory, execute means "allowed to enter/
  traverse it," not "run as a program." Without it you can't actually get
  into the folder to reach anything inside, even with read access. On the
  `authorized_keys` **file**, `600` gives the owner read + write only, no
  execute — because the file is just data `sshd` reads, never a program
  that gets run, so execute permission would be meaningless there.
  `chown` is the separate command that changes who *owns* a file/folder
  (needed after copying `root`'s `authorized_keys` into the new user's
  home directory, since the copy was still owned by `root`).

- **Group changes need a fresh session**: after `usermod -aG docker
  $USER` (or the earlier `sudo` group addition), an already-open SSH
  session doesn't pick up the new group membership — hit "permission
  denied" against the Docker socket until reconnecting with a new SSH
  session.
