# Caddy

Sources are cited inline. This is all fetched from Caddy's official docs
([caddyserver.com/docs](https://caddyserver.com/docs/)), not general
knowledge, since this project hasn't used it before now.

## What it is, and why it's in this project

Caddy is a web server, described in its own docs as "a server of servers,"
but the one feature that matters for this project is **automatic
HTTPS**. Point Caddy at a domain name, and it will get a real, trusted TLS
certificate (from Let's Encrypt, or ZeroSSL as a fallback) and renew it
automatically, forever, with no manual steps
([source](https://caddyserver.com/docs/automatic-https)).

This is the piece that turns "the app is reachable over plain HTTP" into
"the app is reachable over real HTTPS," without paying for a certificate
or running any renewal scripts yourself. Caddy sits in front of an app as
a **reverse proxy**: the public internet talks to Caddy over HTTPS on port
443, and Caddy forwards (proxies) that traffic internally to the app on
whatever port it's actually listening on.

## The Caddyfile

Caddy's config file, called a `Caddyfile`, is deliberately terse. The
minimal reverse-proxy config
([source](https://caddyserver.com/docs/quick-starts/reverse-proxy)):

```
example.com

reverse_proxy :9000
```

- **Line 1** is the site address, the domain Caddy should serve. This is
  also what *triggers* automatic HTTPS: "Caddy will serve your proxy over
  HTTPS automatically and by default if it knows the hostname (domain
  name)" ([source](https://caddyserver.com/docs/automatic-https)). Using
  `localhost` instead gives you a self-signed certificate, not a real
  trusted one. A real domain name is what unlocks the real cert.
- **`reverse_proxy :9000`** forwards incoming requests to whatever's
  listening on port 9000, the app's own port, whether that's on the same
  machine or a container reachable by name on the same Docker network.

A domain obtained via sslip.io (see `docs/concepts/sslip-io.md`) works
just as well as a purchased one for that first line, since Caddy only
cares that the domain's DNS actually points at the server.

## Requirements for the automatic HTTPS to actually work

From the docs
([source](https://caddyserver.com/docs/automatic-https)):

- The domain's DNS (A/AAAA record) has to actually point at the server.
  This is exactly what sslip.io provides for free, without owning a real
  domain.
- Ports 80 and 443 need to be open and reachable from the public internet.
  A firewall in front of the server has to allow both, not just
  whatever port the app itself listens on.
- Caddy needs a persistent, writable directory to store the certificate
  it obtains, so it doesn't have to re-request a new one every restart.

Once that's satisfied, Caddy automatically obtains and renews
certificates, and redirects any plain HTTP request to HTTPS on its own.

## Running it, CLI and Docker

Core CLI commands
([source](https://caddyserver.com/docs/command-line)):

- **`caddy run`** runs Caddy in the foreground, blocking. Useful for
  seeing logs directly, similar to `docker compose up` without `-d`.
- **`caddy start`** runs Caddy in the background and returns your
  terminal immediately.
- **`caddy stop`** gracefully shuts down a running Caddy process.
- **`caddy reload`** applies a changed config to an already-running
  Caddy instance without downtime. This is the normal way to pick up
  Caddyfile changes in production, instead of stopping and starting.
- **`caddy fmt`** auto-formats a Caddyfile.
- **`caddy validate`** checks a config file for errors without running
  it.

In a Docker Compose setup, Caddy typically runs as its own service using
the official `caddy` image rather than the bare binary directly. Key
points from Docker Hub's image docs
([source](https://hub.docker.com/_/caddy)):

- Expose ports 80 and 443 (plus 443/udp for HTTP/3).
- Mount the `Caddyfile` into the container rather than baking it into a
  custom image, which keeps the config editable without rebuilding.
- Mount a **named volume** at `/data`. This is where Caddy stores the
  certificate and key it obtains. It has to persist across container
  restarts, or Caddy would have to re-request a new certificate every
  time the container recreates. `/config` is a second, optional-but-
  recommended volume for Caddy's own config state.
