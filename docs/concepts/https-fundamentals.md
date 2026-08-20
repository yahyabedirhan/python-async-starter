# HTTPS fundamentals: the problem behind Caddy, sslip.io, and Let's Encrypt

This is a step back from any one tool, to lay out the actual problem being
solved and where each piece (Caddy, sslip.io, Let's Encrypt) fits. It's
general knowledge and background explanation, not tied to one fetched
source, unlike `docs/concepts/caddy.md` and `docs/concepts/sslip-io.md`,
which cite the specific tool docs.

## The real problem is actually two separate problems

"Set up HTTPS" sounds like one task, but it's really two independent
problems that got bundled together, historically solved by two completely
different industries:

1. **Naming**: how does a person reach your server using a memorable name
   (`example.com`) instead of a raw IP address (`167.233.107.219`)? This
   is what **DNS** (Domain Name System) and domain registrars solve. It
   has nothing to do with encryption or security by itself.

2. **Trust and encryption**: once a browser reaches your server, how does
   it know it's really talking to *your* server and not an impostor
   intercepting the connection, and how is the traffic between them kept
   private from anyone watching the network in between? This is what
   **TLS certificates** and **Certificate Authorities** solve.

You need both to get a working `https://example.com`. That's the whole
reason this feels like a pile of separate tools glued together, because
it genuinely is solving two unrelated problems, and each tool in this
project's plan handles one side:

- **sslip.io** → solves the naming problem, for free, without buying a
  domain.
- **Let's Encrypt** → solves the trust/encryption problem, by issuing a
  certificate, for free, automatically.
- **Caddy** → the web server that actually *uses* both of the above: it
  requests the certificate from Let's Encrypt, serves traffic encrypted
  with it, and forwards (proxies) the decrypted request to the FastAPI
  app.

## Terminology, plain

- **SSL vs. TLS**: SSL (Secure Sockets Layer) was the original protocol
  for encrypting a connection. It's old and has known security flaws, and
  it was formally replaced by **TLS** (Transport Layer Security) years ago.
  Nobody actually uses SSL anymore, but the name stuck around out of
  habit. When people say "SSL certificate" today, they mean a TLS
  certificate. Same idea, the old brand name just never went away.

- **Certificate**: a small signed file that binds a domain name to a
  cryptographic key, and proves who signed it. It's what lets a browser
  verify "this really is `example.com`" and gives it the key material
  needed to encrypt the connection.

- **Certificate Authority (CA)**: an organization trusted to sign
  certificates. Browsers and operating systems ship with a built-in list
  of CAs they trust automatically (a "root store"). Let's Encrypt is one
  such CA, a nonprofit one, specifically created to make certificates
  free and automatable.

- **DV / OV / EV** are three levels of how much a CA verifies before
  issuing a certificate:
  - **DV (Domain Validated)**: the CA only checks that you control the
    domain (e.g. by asking you to publish a specific file on it, or add a
    specific DNS record). Fast, fully automatable, free with Let's
    Encrypt. This is what almost the entire internet uses today,
    including large companies.
  - **OV (Organization Validated)**: the CA additionally verifies your
    business is a real, registered organization. Costs money, takes
    longer, not automatable.
  - **EV (Extended Validation)**: rigorous legal/business vetting, used
    to trigger a green address-bar indicator in old browsers. Browsers no
    longer visually distinguish it from DV, so its practical value today
    is mostly historical.
  - For this project (and for most websites): **DV is completely
    sufficient**. It provides identical encryption strength to OV/EV.
    The difference is only about identity vetting, not security.

- **ACME**: the automated protocol Let's Encrypt uses to issue and renew
  certificates without a human filling out a form. This is the specific
  thing that makes "automatic HTTPS" possible. Caddy has an ACME client
  built in, so it can talk to Let's Encrypt directly.

## What ACME actually proves, and how

A domain-validated certificate doesn't prove identity or ownership in any
legal sense. It proves one specific, narrower thing: that whoever is
requesting the certificate is also the one actually running the server
that the domain currently resolves to. The most common way Caddy
demonstrates that is the **HTTP-01 challenge**, a public, standardized
part of the ACME protocol (RFC 8555), not something proprietary to either
side:

1. Caddy asks Let's Encrypt for a certificate, sending the domain name
   and its own **account key**, a key pair Caddy generated the first
   time it registered with Let's Encrypt, separate from the certificate's
   own key.
2. Let's Encrypt replies with a random, one-time **token**.
3. Caddy combines that token with a hash of its account key (this
   combined value is called a "key authorization") and serves it at a
   specific, predictable URL on the domain:
   `http://<domain>/.well-known/acme-challenge/<token>`.
4. Let's Encrypt makes its own independent request to that exact URL. It
   doesn't trust anything Caddy told it, it goes and checks itself,
   and compares the response against what it expects. If it matches, it
   signs and issues the certificate.

The reason step 4 actually proves something: the account key half of the
key authorization never leaves Caddy's own private state, so only the
server that holds that key could ever produce the matching value. A
different server, sitting at a different IP, has no way to answer
correctly even if it somehow saw the token, since it doesn't have Caddy's
account key. So the guarantee isn't "this person legally owns this
domain," it's "whatever machine is actually answering requests for this
domain right now is the same machine that's asking for the certificate."
That's also exactly why pointing a domain at the wrong server (or a
domain that doesn't resolve to your own server at all, like a mismatched
sslip.io hostname) makes certificate issuance fail cleanly, rather than
succeed incorrectly: the party requesting the cert and the party actually
answering on that domain have to be provably the same machine.

## Ports 80 and 443

A port is just a number identifying which service on a machine a
connection should go to. A server can have many things listening on
different ports at once. Port **80** is the default for HTTP, and port
**443** is the default for HTTPS. "Default" specifically means: browsers
fill them in automatically when they're left out of a URL.
`http://example.com` is really `http://example.com:80`, and
`https://example.com` is really `https://example.com:443`, the browser
just never shows it. Any other port (like `:8000`) has to be typed
explicitly, because there's no standard convention for the browser to
assume.

80 and 443 belong to a reserved range called the **well-known ports**
(0–1023), assigned by IANA (the body that registers standard internet
protocol numbers) to long-established services, such as 22 for SSH, 25
for email (SMTP), and 80/443 for the web. On Linux, there's a practical
consequence of that range: only the root user, or a process explicitly
granted the capability, is normally allowed to bind to a port below 1024.
That's part of why an app process usually listens on something like
`:8000` internally, while a dedicated web server or reverse proxy is the
one that actually binds 80/443 and forwards traffic inward.

## The traditional (manual) way

Before tools like this existed, getting HTTPS working looked like:

1. Buy a domain from a registrar.
2. Buy a certificate from a CA (often a paid one), submitting a
   certificate request and proving domain ownership by hand.
3. Download the issued certificate and manually install it in your web
   server's config (e.g. Nginx or Apache).
4. Restart the web server.
5. Remember to repeat steps 2–4 before the certificate expires. Paper
   certificates used to last 1–2 years; Let's Encrypt's free ones last
   only 90 days, specifically to force automation.

Missing step 5 is a classic, very common way production sites break.
Users see a broken padlock or a hard connection error until someone
notices and renews it by hand.

## The modern, automated way (what this project uses)

Caddy replaces steps 2–5 entirely: point it at a domain, and it requests,
installs, and renews the certificate itself, forever, using ACME to talk
to Let's Encrypt. sslip.io replaces step 1 (buying a domain) with a free
hostname that's mathematically derived from the server's own IP address.

## Alternatives at each layer

Worth knowing these exist, even though this project isn't using them.
Useful for recognizing the landscape:

**Naming (alternative to sslip.io)**:
- Buying a real domain from a registrar (Namecheap, Cloudflare Registrar,
  etc.), the standard path for anything long-lived or public-facing.
- Similar free "IP-in-hostname" services like `nip.io`, doing the same
  trick as sslip.io.
- A cloud provider's own auto-assigned DNS name, if one is offered (some
  platforms give you a `something.provider.com` name for free).

**Certificate issuance (alternative to Let's Encrypt)**:
- **ZeroSSL** is Caddy's own automatic fallback if Let's Encrypt fails.
  It works the same way (free, automated, DV).
- Paid CAs (DigiCert, Sectigo, GlobalSign) are used when an organization
  specifically wants OV/EV validation, e.g. for regulatory or brand
  reasons. Functionally the same encryption; different vetting.

**Serving + automation (alternative to Caddy)**:
- **Nginx + Certbot** is the older, more manual combination: Nginx as the
  web server, Certbot as a separate tool that requests/renews certs from
  Let's Encrypt and edits Nginx's config, usually run on a timer (cron).
  Two separate tools that have to be kept in sync, versus Caddy doing
  both natively.
- **Traefik** is a reverse proxy comparable to Caddy, also with automatic
  HTTPS built in via ACME. Especially popular in Docker/Kubernetes setups
  where services come and go dynamically.
- **A CDN/proxy in front of the origin** (e.g. Cloudflare's proxy mode) is
  a different architecture entirely: the CDN terminates HTTPS at its own
  edge servers (using its own certificate) and the connection from the
  CDN back to your actual server can even stay plain HTTP. This trades
  "you manage the cert" for "someone else's infrastructure sits between
  users and your server."

See `docs/concepts/caddy.md` and `docs/concepts/sslip-io.md` for the
tool-specific mechanics of how each piece is actually configured.
