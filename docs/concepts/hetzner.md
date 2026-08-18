# Hetzner Cloud

This is the fundamentals doc for Hetzner, written before creating anything
in the console. Sources are cited inline since none of this is general
knowledge for this project — it's all from Hetzner's own docs, fetched
while writing this.

## Account vs. Project

Your Hetzner account is the top level — billing, login, and account-wide
settings live there. A **Project** is a container underneath the account
that groups a set of infrastructure together: servers, firewalls, SSH
keys, networks, volumes, etc. Hetzner's own docs describe it as having "a
dedicated set of members and resources, whereas each member has a role,
which determines what they are allowed to do"
([source](https://docs.hetzner.com/)). In practice, projects are how you
separate infrastructure that shouldn't mix — e.g. a "personal-learning"
project vs. a "work" project — rather than something with deeper technical
meaning. Names must be unique *within* a project (a server name, for
example, only has to be unique per-project, not account-wide).

You don't need more than one project to get started. One project is enough
to hold everything this project needs (the VM, its firewall, its SSH key).

## What lives inside a project

The entities you'll see in the console sidebar, and what each is for:

- **Servers** — the actual VMs. This is the core resource; everything else
  exists to support or protect a server.
- **SSH Keys** — a public key uploaded to Hetzner so it can be injected
  into a server at creation time, for key-based login instead of a mailed
  root password. Important constraint: an SSH key has to be attached
  *when the server is created* — "it is no longer possible to add an SSH
  key via the Hetzner Console" after the fact
  ([source](https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/)).
  If you skip this step, Hetzner instead emails you a one-time root
  password, and you'd need to change SSH's `PreferredAuthentications`
  setting to `password` to log in that way
  ([source](https://docs.hetzner.com/cloud/servers/getting-started/connecting-to-the-server/)).
- **Firewalls** — a traffic controller you attach to one or more servers.
  Inbound traffic is blocked by default unless a rule explicitly allows
  it; outbound traffic is allowed by default unless a rule restricts it.
  A firewall can be attached directly to a server, or automatically to any
  server matching a label selector. Limits: up to 5 firewalls per server,
  50 firewalls per project, 500 effective rules per firewall
  ([source](https://docs.hetzner.com/cloud/firewalls/overview/)).
- **API Tokens** — found under Security → API Tokens inside a project.
  Lets you manage that project's resources (servers, volumes, load
  balancers, ...) through the Hetzner Cloud API instead of the console —
  relevant later for scripting deploys, not needed for the guided
  walkthrough
  ([source](https://docs.hetzner.com/cloud/api/getting-started/generating-api-token/)).
- **Volumes, Load Balancers, Networks, Snapshots, Placement Groups** —
  additional infrastructure you can attach to a server at creation time or
  later (extra block storage, private networking, backups, etc). None of
  these are needed for Phase 1's scope — noted here so the names are
  recognizable, not because they're being used yet.

## What creating a server actually involves

From Hetzner's own getting-started guide
([source](https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/)):
in a project, **Servers → Add server**, then choose:

1. **Location** — which physical datacenter region. Pick whichever is
   geographically closest to you or your users.
2. **Image** — the operating system (a base OS image, a snapshot, or an
   app with software preinstalled).
3. **Type** — the server's size/plan (CPU, RAM, disk). Can be resized
   later.
4. **Networking** — public IPv4 + IPv6, just one, or private-network-only.
5. **SSH Key** — must be added now (see above).
6. **Additional options** — Volumes, Firewalls, automatic Backups,
   Placement Groups, Labels, Cloud-init scripts. Optional at this stage.
7. **Name** — unique within the project.

Hetzner provisions the server in under a minute; the public IPv4 shows up
on the server's overview page once it's ready.

## What Phase 1 actually needs from this

Per `docs/progress.md`, Phase 1's remaining Hetzner steps are: create the
VM, harden it (SSH key-only login, non-root user, Hetzner Cloud Firewall),
install Docker + Compose, deploy, verify it's reachable, then add Caddy +
sslip.io for HTTPS. Mapping that onto the entities above:

- One **Project** (new, dedicated to this project).
- One **Server** (small type is enough — this is a learning demo, not a
  production workload).
- One **SSH Key**, added at creation time, so there's no mailed root
  password to deal with.
- One **Firewall**, restricting inbound traffic to just SSH (22) and
  whatever port the app/Caddy needs — matching the "only 22 and the app
  port open" scope already decided in `docs/journal.md`.
- No Volumes, Load Balancers, private Networks, or Snapshots — out of
  scope for Phase 1.
