# Choosing a language/runtime for a server

How Python, JavaScript/Node, Java, and Go each handle the concurrency
problem covered in [docs/concepts/concurrency-models.md](concurrency-models.md), and why C/C++
usually isn't the obvious choice it might seem for a typical web backend.

## Per-language concurrency models, compared

### Python

Python has the GIL (see [docs/concepts/python-concurrency.md](python-concurrency.md)): only one
thread ever runs Python bytecode at a time. That rules out threads as a way
to speed up CPU-bound work, so you need separate processes for that,
regardless of whether the rest of your code is sync or async.

For I/O-bound work, which is the vast majority of a typical web backend,
Python gives you a real choice. You can run a WSGI app (classic
Flask/Django) on a thread or process pool, or you can run an ASGI app
(`asyncio`, Starlette, FastAPI, see [docs/concepts/python-web-servers.md](python-web-servers.md)) on a
single-threaded cooperative event loop. This project picked the
event-loop route on purpose, since learning meaningful `asyncio` usage is
one of its goals.

### JavaScript / Node

Node's actual JavaScript code is always single-threaded. There's no
GIL-style decision to make, because Node never offered OS-thread
concurrency for JS to begin with. All of Node's concurrency comes from the
event loop handing I/O off to the kernel, plus a small background thread
pool inside Node itself (called libuv) for the handful of things the
kernel can't do non-blockingly, like some filesystem calls. See
[docs/concepts/javascript-event-loop.md](javascript-event-loop.md) and
[docs/concepts/javascript-runtimes.md](javascript-runtimes.md) for the full mechanics.

### Java

Java's traditional model is the OS-thread-per-request approach covered in
[docs/concepts/concurrency-models.md](concurrency-models.md): one real OS thread handles one
connection, kept to a bounded thread pool. Combined with the classic
blocking I/O APIs (`java.io`, `java.net`), this means a network call
genuinely blocks the OS thread that made it. The thread just sits there,
doing nothing, until the response arrives. This worked in production for
two decades, but it runs into the same C10K-style ceiling as any
thread-per-connection design once concurrency gets high enough.

Java also has a second, older way around this: `java.nio`, meaning
non-blocking sockets plus a `Selector` you poll yourself, conceptually the
same epoll-style readiness notification covered in
[docs/concepts/concurrency-models.md](concurrency-models.md)'s appendix. It works, but it's a
manual, callback-driven API that most application code doesn't touch
directly. Frameworks like Netty build their own event loops on top of
it instead.

The newer, more direct answer is **virtual threads**, finalized via
[JEP 444](https://openjdk.org/jeps/444) and described in
[Oracle's own docs](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html):
lightweight threads implemented by the Java runtime itself, multiplexed
onto a small pool of real OS "carrier" threads, explicitly compared to how
virtual memory maps a huge virtual address space onto limited physical
RAM. The docs are careful to note "virtual threads are not faster threads;
they do not run code any faster than platform threads. They exist to
provide scale (higher throughput), not speed (lower latency)." That's the
same trade-off an event loop makes, reached through a completely different
mechanism (still literally threads, just cheap ones).

The genuinely useful part: virtual threads reuse the *same* classic
blocking `java.io`/`java.net` APIs, with no new syntax and no `Selector`
to manage by hand. Per the [`java.lang.Thread` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html):
"Locking and I/O operations are examples of operations where a carrier
thread may be re-scheduled from one virtual thread to another." So a
network call on a virtual thread frees up its carrier OS thread while
waiting, the same *effect* Go's goroutines achieve. Worth flagging
honestly, though, that Oracle's public docs describe that effect without
spelling out the exact non-blocking mechanism underneath it, unlike Go
(next section), whose own source code names the mechanism directly.

### Go

Goroutines are Go's version of the same idea, and the official Go FAQ
([go.dev/doc/faq](https://go.dev/doc/faq)) is explicit that they were
built to dodge this whole trade-off: "very cheap: they have little
overhead beyond the memory for the stack, which is just a few
kilobytes... It is practical to create hundreds of thousands of goroutines
in the same address space." The Go runtime multiplexes goroutines onto a
small number of real OS threads itself, transparently. You write plain,
ordinary-looking blocking-style Go code, with no `async`/`await` keywords
anywhere in the language, and the runtime handles making it concurrent
underneath.

Unlike Java's virtual threads, Go's own source names the exact mechanism
publicly. The doc comment at the top of the runtime's network poller
([`runtime/netpoll.go`](https://github.com/golang/go/blob/master/src/runtime/netpoll.go))
states: "Integrated network poller (platform-independent part). A
particular implementation (epoll/kqueue/port/AIX/Windows) must define the
following functions." That's the same readiness-notification mechanism
from [docs/concepts/concurrency-models.md](concurrency-models.md)'s appendix, just built into
the Go runtime itself instead of exposed to the programmer. When a
goroutine calls something like `conn.Read()` and no data is ready yet, the
goroutine is parked and its OS thread is freed to run other goroutines;
the netpoller wakes it back up once the kernel reports the socket is
ready.

So, directly: **neither Go nor Java has `async`/`await` keywords**, and
**neither creates a brand-new OS thread for every I/O call**. Go never
did; goroutines were designed around the netpoller from day one. Java only
does, in the literal, costly sense, if you're on the traditional
platform-thread model with classic blocking I/O; virtual threads (or
manual NIO) avoid it, reusing the ordinary blocking APIs while freeing the
underlying OS thread while waiting.

## How similar are goroutines and Java's virtual threads, really?

Similar in category and motivation, not identical in mechanism:

- **Both** are lightweight, runtime-managed threads multiplexed onto a
  small pool of real OS threads, both let you write ordinary blocking-style
  code without `async`/`await` syntax, and both are explicitly a
  throughput trade-off rather than a speed one.
- **Age and status differ.** Goroutines have been core to Go since its
  2009 release; there's no other concurrency primitive in idiomatic Go.
  Virtual threads are recent (Java 21, via JEP 444) and sit *alongside*
  Java's older platform threads rather than replacing them; a Java
  codebase can mix both.
- **API surface differs.** Virtual threads were deliberately built as a
  drop-in for the existing `java.lang.Thread`/`ExecutorService` APIs. Go's
  goroutines aren't an addition to a prior thread API at all; `go
  func(){}` plus channels is a distinct concurrency model from the start.

Go and Java's virtual threads arguably represent the industry converging
on "give me cheap concurrency without making me restructure my code into
async/await," which is a real ergonomic argument in their favor over the
Python/JS approach. The trade-off there is runtime/language complexity (a
scheduler baked into the language runtime itself) instead of
programmer-visible complexity (colored functions, `await` everywhere).

## Why not just write servers in C or C++?

This one is general engineering knowledge rather than something pulled
from an official doc. A few compounding reasons this isn't the obvious
choice it might seem:

- **Manual memory management is a direct, ongoing source of severe bugs.**
  C/C++ require you to explicitly allocate and free memory yourself,
  correctly, in every code path, forever. A large fraction of historically
  serious security vulnerabilities (buffer overflows, use-after-free,
  dangling pointers) trace directly back to this. The language gives the
  programmer full control and full responsibility, with no safety net.
  Python, JavaScript, Go, and Java all use automatic memory management
  (garbage collection or, for Go, escape analysis + GC) specifically to
  remove this entire bug category.
- **The bottleneck in most web backends usually isn't CPU speed at all.**
  As established in [docs/concepts/concurrency-models.md](concurrency-models.md), a typical
  request spends most of its time *waiting*, whether that's on a
  database, another service, or the network. Shaving microseconds off
  request-handling logic with a faster compiled language barely matters if
  the request is going to spend 50ms waiting on Postgres regardless. Raw
  execution speed matters far more for genuinely CPU-bound workloads
  (video encoding, scientific computing, game engines) than for I/O-bound
  CRUD APIs, which is most of what web backends actually are.
- **Development velocity is a real, first-class cost.** C/C++ have no
  built-in high-level abstractions for HTTP, JSON, or database access, so
  you either build them yourself or rely on external libraries with far
  less polish than what Python/JS/Go/Java's ecosystems offer. Slower to
  write, slower to iterate, and every manual memory-management mistake is
  a potential production incident instead of a caught exception.
- **Go and Rust exist as the actual "compiled and fast, but not C++"
  middle ground** for teams that do need more raw performance than
  Python/JS/Java offer. Go specifically (see above) gets both
  memory-safety (garbage collected) and genuinely cheap, runtime-managed
  concurrency, without giving up compiled-language performance. This is
  why Go, not C++, is the usual answer today when a team outgrows
  Python/Node for a specific high-throughput service, rather than reaching
  straight for manual memory management.
