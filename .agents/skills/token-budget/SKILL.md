# SKILL: Token Budget

## Purpose

Estimate token cost before reading a file, choose lazy-load over full-read, and keep per-turn context within budget.

## When to Use

- Before reading any file > 200 lines.
- When the user complains about long answers or slow turns.
- During `token-auditor` workflow.

## Heuristics

| Artefact | Tokens / line (rough) | When OK to read whole file |
|---|---|---|
| Python source | 10–14 | < 150 lines AND directly relevant |
| Markdown docs | 8–12 | < 80 lines AND no in-file TOC available |
| HTML / Jinja templates | 12–18 | almost never — read by `{% block %}` |
| YAML / TOML / requirements | 6–8 | always OK if < 60 lines |
| Test files | 10–14 | only when fixing the test itself |
| `node_modules` / `mcp-servers` | — | **NEVER** |

## Lazy-Load Pattern

1. **Map first** — `grep -n '<symbol>' <path>` returns line numbers; read only `±20` lines.
2. **Section-only** — for long MDs (e.g. `docs/API.md`), `grep -nE '^##? ' <file>` to find anchors, then `sed -n 'A,Bp'` for one section.
3. **Index then leaf** — read `docs/INDEX.md` (≤ 60 lines), then only the leaf doc the index points to.
4. **Tail-only logs** — `tail -50 docs/progress.md`. Never `cat docs/progress.md`.

## Output Discipline

- Lead with the answer / diff. No preambles.
- Bullets > prose. One claim per bullet.
- For compare-and-decide tasks, prefer a 3-column table over paragraphs.
- Code: only the diff, no surrounding unchanged lines, no "now we …" comments.

## Caching

- Static project-facts (stack, sources of truth, invariants) live in `{{PROJECT_FACTS}}` — they're cacheable across turns.
- Few-shot examples live in `.agents/prompts/shl-optimizer.fewshot.md` — load only on first activation per session.

## Self-Check Checklist (run before each tool call that reads a file)

- [ ] Do I need the whole file, or one section?
- [ ] Is there a `grep`/`sed` command that gets me the same answer in 1/10 the tokens?
- [ ] Is this file in `forbidden_full_read` (see prompt v2.0)?
- [ ] Will the next turn need this file again? If yes, prefer a one-time index pass over re-reading.
