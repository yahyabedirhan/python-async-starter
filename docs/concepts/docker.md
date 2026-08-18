# Docker

## What it is

Docker packages an app together with everything it needs to run: system
libraries, the Python interpreter, all the dependencies. That package is
called an **image**. When you run an image, it starts a **container**,
which is just an isolated running process. It's lighter than a full virtual
machine because it shares the host machine's kernel instead of virtualizing
a whole new one.

## Dockerfile basics used here

- **Base image**: we start from `python:3.12-slim-trixie`. The `slim`
  version is smaller because it leaves out compilers and dev tools we don't
  need at runtime.
- **Layers**: every line in a Dockerfile (`RUN`, `COPY`, etc.) creates a
  cached layer. If a layer's inputs haven't changed, Docker skips
  re-running it on the next build. That's why we install dependencies in a
  separate step before copying our code — see `docs/concepts/uv.md`. It
  means editing `main.py` doesn't force Docker to reinstall everything.
- **`EXPOSE 8000`**: this just documents which port the app listens on. It
  doesn't actually make the port reachable by itself.
- **`CMD`**: the command that runs when the container starts. Ours is
  `fastapi run main.py --port 8000`.

## Running as a non-root user

Where this comes from: Docker's own official best-practices page,
[docs.docker.com/build/building/best-practices](https://docs.docker.com/build/building/best-practices/).
It says: *"If a service can run without privileges, use `USER` to change to
a non-root user."* This isn't a FastAPI thing, it's general Docker advice.

Why it matters: if you don't set a `USER`, the process inside the container
runs as root. That's the same root as on the host machine, just inside a
separate container. Containers keep things isolated, but that isolation
isn't a perfect wall. If someone finds a way to exploit the app, and the
process is running as root inside the container, it becomes easier for them
to break out and get root access on the actual host machine too. Running as
a normal, unprivileged user means that even if something goes wrong, the
damage is more contained. It's one safety layer among several, not a
complete fix by itself.

Here's what we added to the Dockerfile:

```dockerfile
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser
```

We picked the numbers 1000 for the user ID and group ID on purpose, instead
of letting the system pick automatically. That way the ID stays the same
every time we rebuild the image, even if the base image changes later. The
name `appuser` doesn't mean anything special — Docker's own example in
their docs just uses `postgres` as the name, since that matches the service
they were containerizing.

## Do these user ID numbers need to be unique across projects?

No. This works differently than something like a network port. Ports are
exclusive — only one program on your machine can use port 8000 at a time,
which is why different projects need different port numbers. User IDs
don't work that way. They're not a limited, shared resource. Many
containers can each use the number 1000 as their internal user ID at the
same time, with zero conflict, because each container has its own isolated
world by default.

There's one exception worth knowing about: if you mount a folder from your
host machine into a container (so the container can read or write real
files on your computer), then the user ID inside the container does matter
for file permissions on that shared folder. But we're not doing that in
this project, so it doesn't apply here.

One honesty note: Docker's docs confirm the basic mechanics (what `USER`
does, that root is the default), but I couldn't find one single sentence in
their docs that directly says "user IDs aren't exclusive like ports." That
part is my own reasoning based on how container isolation generally works,
not a direct quote from their documentation.

## How to check it worked

```bash
docker exec <container> whoami   # should print: appuser
docker exec <container> id       # should print: uid=1000(appuser) gid=1000(appuser)
```

## Running it

The project is run with Docker Compose rather than a raw `docker build` +
`docker run` — see `docs/concepts/docker-compose.md` for why and how.
Everything above about the Dockerfile itself (layers, the base image, the
non-root user) still applies unchanged; Compose just orchestrates the same
image.
