# Agent Instructions

## Git commit convention

Use Conventional Commits prefixes: `feat:`, `fix:`, `docs:`, `style:`,
`refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:`, `revert:`.

- Subject line (prefix + summary): max 50 characters.
- Always lowercase — even proper nouns/product names (e.g. "fastapi", not
  "FastAPI").
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
of use — don't just state the recommendation. This lets the source be
revisited later. If something instead comes from general/training
knowledge rather than a fetched source, it's fine to say that too when it's
relevant (e.g. the info may be stale).

## Documentation style (docs/ folder)

Write in plain, natural sentences — the way you'd explain something out
loud to a person, not compressed notes. Prefer several short sentences over
one dense sentence packed with clauses. Avoid unexplained jargon; if a term
is needed, explain it in plain words the first time it's used. Goal: it
should be understandable half-asleep at 3am, not just technically correct.

This applies to `docs/journal.md` and `docs/concepts/*.md`. It does not
mean padding things out — stay focused, just don't sacrifice clarity for
brevity.
