# Decision Log

> Older entries are archived verbatim at `docs/archive/2026-Q2.md`:
> - `## Decision Log (rotated 2026-05-04)` — 8 entries 2026-04-23 → 2026-04-29.
> - `## Decision Log (rotated 2026-05-13)` — 3 entries 2026-04-30, 2026-05-01
>   ×2, rotated per TIK-89 / T14. Forward-contracts blocks preserved
>   verbatim under `## Active Forward Contracts` below.
> - `## Decision Log (rotated 2026-05-13, part 2 — TIK-92)` — 8 ADRs
>   2026-05-03 → 2026-05-11, rotated per TIK-92 to hold this file under
>   ~200 lines. Forward-contracts blocks of the 3 archived ADRs that
>   carried them (2026-05-11 task-formulation, 2026-05-05 Inspector,
>   2026-05-03 TIK-51) are preserved verbatim under `## Active Forward
>   Contracts` below.
>
> Restore via `git revert` if needed.

## Active Forward Contracts

> Forward-contract stubs from ADRs that have been rotated into
> `docs/archive/2026-Q2.md`. Kept here so agents never have to read the
> archive to know what *must not* regress. Verbatim — do not summarise.

**From 2026-04-30: Token-efficiency pass** (archive):

- `Flask-Compress` MUST stay disabled in `TESTING` (otherwise `response.data`
  in test clients comes back as compressed bytes and assertions break).
- `mcp-servers/` MUST remain in `.gitignore`. Don't `git add mcp-servers/`.
- `paginate_query` is the canonical pagination helper. New listing endpoints
  should go through it so they pick up `?fields=` for free.

**From 2026-05-01: Sub-agents + skills + SHL-OPTIMIZER prompt v2.0** (archive):

- `shl-optimizer.fewshot.md` MUST be loaded only via `@include` from
  Instructions §4 of `shl-optimizer.prompt.md` — never inlined into the
  system prompt and never duplicated in the `## Few-shot` section of the
  prompt file.
- `docs/archive/<period>.md` is the **only** destination for rotated
  `progress.md` / `decisionLog.md` entries. Never `git rm` historical
  records.
- `docs/INDEX.md` MUST be updated whenever an archive file is added under
  `docs/archive/`.
- `token-auditor` and `doc-curator` MUST NOT modify source code or test
  files. If a token-waste fix requires source/test changes, hand off to
  `coder`.
- `progress.md`, `decisionLog.md`, `docs/API.md`, and `mcp-servers/**` are
  on the `forbidden_full_read` list — agents must use `grep -n` +
  section-only reads.

**From 2026-05-01: Repo hygiene — untrack mcp-servers/, dev.db, .env** (archive):

- Never re-add `mcp-servers/` to tracking. Reinstall via `make mcp-install`
  (or `cd mcp-servers && npm install`).
- Never re-add `dev.db`. Recreate via `make init-db`.
- Never commit `.env`. Use `.env.example` as the only template.

**From 2026-05-11: Task-formulation skill + thin Obsidian wiki (no content duplication)** (archive, rotated per TIK-92):

- New skills MUST be added to AGENTS.md § 3 and to
  `docs/INDEX.md` (already done for `task-formulation`).
- New canonical docs SHOULD get a thin wiki note that summarises +
  links — but only when the doc covers a distinct domain. Don't
  invent wiki notes for every file.
- `docs/wiki/.obsidian/` is git-ignored (`/.gitignore` 2026-05-11).
  If we ever want a shared vault config (snippets, hotkeys, plugin
  list), revisit and commit a curated subset.

**From 2026-05-05: Inspector-based idempotent column backfill (model ↔ Alembic drift)** (archive, rotated per TIK-92):

- A new test file `tests/test_migrations_schema_parity.py` runs in
  `make test` (and therefore in the `Quality & Tests` CI job). It
  builds a fresh SQLite DB from migrations only, then asserts every
  column in `db.metadata.tables` exists in the inspected schema. Any
  future model column without a matching migration fails the test
  with a precise drift list — *before* it can reach production.

**From 2026-05-03: TIK-51 tech-debt continuation — pip-audit, mypy, coverage gate, e2e in CI** (archive, rotated per TIK-92):

- `pip-audit` policy: `--ignore-vuln <ID>` is allowed only with a one-line
  rationale committed alongside the entry; never silence a CVE without
  documenting why.
- `mypy` policy: prefer `cast()` + narrowing over `# type: ignore`; if you must
  use `# type: ignore`, narrow it (`# type: ignore[arg-type]`) and add a
  one-line reason on the same line.
- E2E policy: the suite is a smoke check, not a feature spec. Keep it under
  ~90s wall-clock; if it grows past that, split per-domain jobs (admin vs
  public vs api) rather than one giant matrix.

---

## 2026-05-13: Leaderboard — sum per-achievement points at full precision; rank on exact float; 3-decimal display only for visual ties in top-10

**Context**: User noticed two managers (Aliaksandr Naidzionau, Юрий
Shestakov) sharing rank 2 with identical displayed totals (`7.80`) on
the live leaderboard, despite owning completely different achievement
sets. Manual arithmetic showed the un-rounded totals were `7.8000` vs
`7.7955` — a real 0.0045 gap. The "tie" was an artefact of
`calculate_achievement_points` rounding every `base * mul` to 2 decimals
before `_build_leaderboard_impl` summed the per-row values, with one
contribution (`0.45 × 0.70 = 0.315`) rounding up to `0.32` and closing
the gap.

**Options considered**:

1. **Sum the rounded `points` (status quo).** Simplest; matches what
   the breakdown panel shows per row; produces phantom ties.
   Rejected — already known to mis-rank.
2. **Sum the rounded `points` and break ties on a secondary key
   (count of TOP1 → count of TOP2 → newest season → name).** Hides
   the actual cause (per-row rounding loss) behind a policy layer and
   introduces a "fairness rule" the players never asked for. Rejected
   in favour of fixing the arithmetic at the source.
3. **Sum the un-rounded `base * mul`; rank on the exact float; render
   2 decimals everywhere.** Mathematically correct, but two adjacent
   rows in the top-10 can still display the same `XX.XX` while
   holding different ranks (e.g. `7.7955` and `7.8000` both render
   `7.80`), which is more confusing than the original "two 2nd
   places". Rejected as the final form.
4. **Sum the un-rounded `base * mul`; rank on the exact float; bump
   *only the visually colliding rows in top-10* to 3 decimals.**
   Chosen. The compact-10 scale (TIK-80) stays compact for 99 % of
   the table; the longer format appears only where it actually
   resolves ambiguity. True ties (same exact total → shared rank)
   stay at 2 decimals because the shared rank pill already conveys
   the tie and a trailing `0` would be noise.
5. **Always render 3 decimals across the whole table.** Considered at
   user prompt. Rejected — most totals collapse to `XX.X00` /
   `X.000` because base points are 1–2 decimal and the active-season
   multiplier is exactly `1.000`, producing trailing-zero visual
   noise that runs against the compact-10 design intent.

**Choice**: Option 4.

**Implementation summary**:

- `services/rating_service.calculate_achievement_points` returns an
  extra un-rounded `points_exact = base * mul` field; the existing
  `points` field stays at 2 dp for the per-achievement breakdown
  panel.
- `services/rating_service._build_leaderboard_impl` sums
  `points_exact` into `total` (`float`, was implicitly `int(0)`) and
  sorts / ranks on the exact value. Strict `==` is correct for the
  rank check because two rows only share a sum when every
  `base * mul` is bit-for-bit identical.
- New helper `_assign_total_display(result)` groups the top-10 rows
  by their 2-decimal display and bumps the entire collision group to
  3 decimals iff those rows hold different ranks. All other rows get
  the compact `XX.XX` format.
- `templates/index.html` renders `row.total_display` for the score
  cell and `data-total` attribute. The breakdown panel data is
  unchanged.

**Reversibility**: Pure additive Python change + one template
substitution. To revert, drop the helper and `points_exact` field and
restore `total_points += parsed["points"]`. No schema migration.

**Regression coverage**:
`tests/test_rating_service.py::TestLeaderboardPrecisionAndTies` — 4 tests
covering phantom tie (different totals same 2dp), true tie (shared
rank stays at 2 dp), non-colliding rows stay at 2 dp, and
`points_exact` exposure.

