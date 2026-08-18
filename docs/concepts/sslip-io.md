# sslip.io

Sourced from the project's own README/docs
([github.com/cunnie/sslip.io](https://github.com/cunnie/sslip.io)), fetched
while writing this — not general knowledge, since this project hadn't used
it before now.

## The problem it solves

Caddy's automatic HTTPS (see `docs/concepts/caddy.md`) needs a real domain
name pointing at the server — Let's Encrypt issues certificates for domain
names, not bare IP addresses. Buying a domain is one way to get that, but
it's unnecessary overhead when you just want HTTPS working on a server you
already have an IP for. sslip.io is a free service that closes that gap
without requiring a domain purchase or even an account signup.

## What it is and how it works

sslip.io is a DNS server "that maps specially-crafted DNS A records to IP
addresses" — its own README's example: `127-0-0-1.sslip.io` resolves to
`127.0.0.1`
([source](https://github.com/cunnie/sslip.io)). The trick is entirely in
the hostname itself: the dots in an IP address are swapped for hyphens,
and stitched onto `.sslip.io`. When something looks up that hostname,
sslip.io's DNS server parses the numbers straight out of the domain name
text and returns them as the IP address — no registration, no config, no
account. Any IP address automatically has a working sslip.io hostname,
because the "database" is just the hostname's own text.

Concretely, for this project's VM at `167.233.107.219`, the matching
sslip.io hostname would be:

```
167-233-107-219.sslip.io
```

You can check this works with `dig` (a command-line DNS lookup tool),
using the example format from their own docs
([source](https://github.com/cunnie/sslip.io)):

```bash
dig 167-233-107-219.sslip.io
```

That should return `167.233.107.219` as the answer.

## Why this satisfies Caddy's requirement

Caddy needs a domain whose DNS actually points at the server. Since
`167-233-107-219.sslip.io` resolves to exactly the VM's own IP — by
construction, not by any manual DNS record we'd have to set up — it
behaves exactly like a real domain pointing at the server, which is all
Let's Encrypt (and therefore Caddy's automatic HTTPS) needs to issue a
real certificate. Both IPv4 (`A` records) and IPv6 (`AAAA` records) are
supported
([source](https://github.com/cunnie/sslip.io)).

## Putting it together with Caddy

Once a server's public IP is stable:

1. Put its sslip.io hostname (e.g. `167-233-107-219.sslip.io`) as the site
   address in Caddy's `Caddyfile`.
2. Caddy sees a real domain name, requests a certificate from Let's
   Encrypt for it, and serves the app over HTTPS at that address.

No DNS provider, no domain purchase, no account — the "domain" is just a
predictable transformation of the IP address itself.
