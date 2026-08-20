# Agent Instructions

## Git commit convention

Use Conventional Commits prefixes: `feat:`, `fix:`, `docs:`, `style:`,
`refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:`, `revert:`.

- Subject line (prefix + summary): max 50 characters.
- Always lowercase, including proper nouns and product names (e.g.
  "fastapi", not "FastAPI").
- If more detail is needed, add a blank line then bullet points:

```
fix: short summary here

- detail one
- detail two
```

## Cite external sources

Whenever a recommendation, command, or pattern comes from an external
source (official docs, a blog post, an MCP tool like Context7, etc.) rather
than general knowledge, say so and link/name the exact source at the point
of use. Don't just state the recommendation. This lets the source be
revisited later. If something instead comes from general/training
knowledge rather than a fetched source, it's fine to say that too when it's
relevant (e.g. the info may be stale).

## Documentation style

Write in plain, natural sentences, the way you'd explain something out
loud to a person, not compressed notes. Prefer several short sentences over
one dense sentence packed with clauses. Avoid unexplained jargon; if a term
is needed, explain it in plain words the first time it's used. Goal: it
should be understandable half-asleep at 3am, not just technically correct.

This applies to `docs/journal.md` and `docs/concepts/*.md`. It does not
mean padding things out. Stay focused, but don't sacrifice clarity for
brevity.

### Voice and tone

- Never use an em dash (—) anywhere in the project, especially `docs/` content.
- Avoid the "label: item, item, item" construction, in section headings.
- Keep sentence structure simple. Prefer ordinary subject-verb-object
  sentences over dense or compressed labels.
- All headers, including the `#` document title, must be concise,
  properly-named noun phrases, not conversational, vague, or
  question-form labels, and not full sentences. Avoid headers like "The
  problem: without an agreement, every pair needs custom glue," "What
  this buys you, concretely," or "is the missing contract actually a
  problem, and how Bun, Deno, Hono, and Elysia handle it." Prefer
  something like "Why a shared contract is necessary" or "Benefits of a
  shared contract" instead.
- Don't use a colon explanator structure in headers (e.g. "JavaScript web
  servers: WinterTC, Bun, Deno, Hono, and Elysia"). Keep the `#` document
  title down to the short subject itself (e.g. "JavaScript web servers"),
  and give `##` section headers a plain noun phrase, not a topic followed
  by a colon and a list or clause.

### Mermaid diagrams

Don't add `<br/>` line breaks inside node text by default. Keep node
labels short and let them sit on one line. Only wrap a label across lines
if it genuinely holds multiple paragraphs or a long block of text that
would otherwise be unreadable as one line, not as a routine habit.

### Concept docs

`docs/concepts/*.md` files must stay reusable on their own, independent of
this specific project's plan. They should never mention phase numbers
("Phase 1," "Phase 3," etc.), this project's roadmap, or "why this matters
for this project" framing. References only go one direction: phase-tracking
docs (`docs/journal.md`, `docs/progress.md`) can point into `docs/concepts/`,
never the other way around. If a concept doc is tempted to explain why
something matters for this project specifically, that explanation belongs
in the journal or progress doc instead, with a link into the concept doc.
