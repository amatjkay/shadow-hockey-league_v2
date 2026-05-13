# Decision Log

> Older entries are archived verbatim at `docs/archive/2026-Q2.md`:
> - `## Decision Log (rotated 2026-05-04)` — 8 entries 2026-04-23 → 2026-04-29.
> - `## Decision Log (rotated 2026-05-13)` — 3 entries 2026-04-30, 2026-05-01
>   ×2, rotated per TIK-89 / T14 to keep the latest 9 active here. The
>   Forward-contracts blocks of all 3 archived entries are preserved verbatim
>   under `## Active Forward Contracts` below.
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

---

## 2026-05-11: TIK-86 — module-level `threading.Lock()` around `build_leaderboard`

**Context**: `tests/integration/test_routes.py::TestConcurrentRequests::test_concurrent_homepage_requests`
intermittently fails with `IndexError: tuple index out of range` (and two
related `NoneType` AttributeErrors). Local stress repro: 200 iterations
of 10-thread concurrent `build_leaderboard()` calls → 29 errors / 2000
calls (~1.5%). Stack traces point to
`sqlalchemy.cyextension.resultproxy._apply_processors`, i.e. a SQLAlchemy
2.0.49 race when the cython result-row processor reads a tuple whose
column count does not match the compiled statement metadata. The race
is real but **does not fire in production today**: `Makefile:145` runs
`gunicorn --workers 4 --sync`, so each request lives in a single-thread
process and the leaderboard query has no in-process peer. The test
client, however, fans 10 threads through one engine and trips it.

**Options considered**:

1. **Switch `joinedload` → `selectinload` in `build_leaderboard`.** Wider
   load pattern, makes N relationship-queries per request, but verified
   experimentally to keep the same race (29 errors / 200 iters under
   identical stress). Rejected.
2. **Disable SQLAlchemy compile cache for this one query
   (`session.connection().execution_options(compiled_cache=None)`).**
   Theory-driven (the cache is the suspected race source) but empirically
   reduced the failure rate without eliminating it. Rejected.
3. **Module-level `threading.Lock()` around the body of
   `build_leaderboard`.** Sync prod workers never contend it; threaded
   test client serialises through it; 5-minute `@cache.cached` keeps
   the hot path off the lock 99% of the time. Verified: 200 iters × 10
   threads = 2000 calls = 0 errors. Chosen.
4. **Delete the flaky test.** Hides the canary; the SQLAlchemy race is
   real and would re-emerge if anyone ever switched gunicorn to
   `--threads N`. Rejected.

**Decision**: Option 3.

- New constant `_LEADERBOARD_LOCK = threading.Lock()` at module level in
  `services/rating_service.py`.
- Public `build_leaderboard()` becomes a 2-line wrapper that holds the
  lock and delegates to `_build_leaderboard_impl()` (private).
  Splitting the body out makes the lock-bypass path explicit if anyone
  ever needs to micro-benchmark the un-serialised version.
- New regression test
  `test_concurrent_homepage_requests_stress` (20 × 10 threads, ~0.4s)
  amplifies the historical 1.5%-per-batch flake rate to a >99%
  per-batch detection, so any future regression that re-introduces the
  race is caught locally before CI.

**Anti-goals locked in by the ticket** (TIK-86 § 4):

- Do not switch from `joinedload` to `selectinload` (same race, slower).
- Do not investigate the root SQLAlchemy bug here — that belongs in an
  upstream issue.
- Do not modify caching, templates, JS, or CSS — they are unrelated.

**Rejected alternatives we may revisit**:

- File an upstream SQLAlchemy issue with the cython-result-processor
  race repro (out of scope per § 4 anti-goals; logged as a follow-up
  in `docs/progress.md`).

## 2026-05-11: Task-formulation skill + thin Obsidian wiki (no content duplication)

**Context**: Owner asked for two related artefacts in the same turn —
(1) a reusable checklist that AI agents must fill in before tackling a
complex task, and (2) an Obsidian-readable wiki over the project. The
repo already has `docs/AI_WORKFLOW.md` (a 19-line English version of
the checklist) and a mature canonical-docs set (`AGENTS.md`,
`PROJECT_KNOWLEDGE.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, …).
Naively, both asks invite duplication: a second checklist file and a
second copy of the architecture docs.

**Options considered**:

1. **Inline the checklist into `AGENTS.md` § 5 and add a 2000-line
   wiki that re-explains the project.** Maximises discoverability but
   creates two new sources of truth that will rot the moment the
   canonical docs change.
2. **Skip the wiki; only add a SKILL.md.** Minimises surface area but
   leaves the owner's "graph view in Obsidian" request unmet.
3. **Make the SKILL.md canonical for the checklist; make the wiki a
   thin navigation layer that only summarises (5–15 lines per note)
   and links to the canonical docs.** Chosen.

**Decision**: Option 3.

- `.agents/skills/task-formulation/SKILL.md` is the **single source of
  truth** for the 4-section checklist (Context / Result shape /
  Definition of Done / Scope & Anti-Goals). The existing
  `docs/AI_WORKFLOW.md` becomes a 19-line pointer at the SKILL so
  the English-language version stays grep-able without duplicating
  the body.
- `.github/ISSUE_TEMPLATE/well-formed-task.md` renders the **same**
  checklist as a GitHub issue form (so the rule applies to
  human-filed tickets too) — but its body is a paraphrase of the
  SKILL, not a fork. Cross-links the SKILL from the top of the
  template.
- `docs/wiki/` is a navigation vault, not a documentation vault.
  Every note is ≤ 60 lines, contains zero copy-pasted content from
  canonical docs, and survives by linking. The owner gets the
  Obsidian graph view; the project keeps `AGENTS.md` /
  `PROJECT_KNOWLEDGE.md` / `docs/ARCHITECTURE.md` / `docs/API.md` as
  the single sources of truth.

**Consequences**:

- Maintenance load stays bounded: when the architecture changes,
  exactly one doc (the canonical one) must be edited. Wiki notes
  point at it and remain accurate "for free".
- The checklist now has a fixed home that agents can `read` /
  `grep` deterministically (`/.agents/skills/task-formulation/SKILL.md`),
  in line with the AGENTS.md § 3 skill discovery pattern.
- The wiki's value is the graph view, not the prose. If a note grows
  past ~60 lines, it should be split or its body should move into a
  canonical doc — flagged at the top of `docs/wiki/README.md`.

**Forward contracts**:

- New skills MUST be added to AGENTS.md § 3 and to
  `docs/INDEX.md` (already done for `task-formulation`).
- New canonical docs SHOULD get a thin wiki note that summarises +
  links — but only when the doc covers a distinct domain. Don't
  invent wiki notes for every file.
- `docs/wiki/.obsidian/` is git-ignored (`/.gitignore` 2026-05-11).
  If we ever want a shared vault config (snippets, hotkeys, plugin
  list), revisit and commit a curated subset.

## 2026-05-05: Inspector-based idempotent column backfill (model ↔ Alembic drift)

**Context**: Six columns declared in `models.py`
(`achievement_types.is_active`, `leagues.is_active`, `countries.is_active`,
`managers.is_active`, `seasons.start_year`, `seasons.end_year`) were never
added by any Alembic migration. Local dev DBs were bootstrapped through
`db.create_all()` so the columns existed; prod was bootstrapped through
Alembic only, so they didn't. The discrepancy was masked by the
leaderboard cache for an unknown duration; PR #73's seed-data mutation
invalidated the cache and the very next homepage request crashed with
`sqlite3.OperationalError: no such column: achievement_types.is_active`.

We needed a column-backfill migration that's safe to run on both:
1. **Prod / staging** — column missing → must add it with the right
   default so existing rows are treated as `is_active = 1`.
2. **Dev DBs** — column already present (from `db.create_all()` or a
   previous hot-fix) → must be a no-op.

**Decision**: Use a **runtime `sa.inspect()` check before each
`add_column`** rather than relying on either `IF NOT EXISTS` (SQLite
doesn't support it for `ADD COLUMN`) or per-environment branching.

```python
@dataclass(frozen=True)
class _MissingColumn:
    table: str
    column: str
    sa_type: type[sa.types.TypeEngine]
    nullable: bool
    server_default: str | None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for spec in TARGET_COLUMNS:
        if _has_column(inspector, spec.table, spec.column):
            continue                       # idempotent — column already there
        new_column = sa.Column(
            spec.column, spec.sa_type(),
            nullable=spec.nullable, server_default=spec.server_default,
        )
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table(spec.table) as batch_op:
                batch_op.add_column(new_column)
        else:
            op.add_column(spec.table, new_column)
```

The `dataclass`-driven spec list is the canonical place to add future
drift fixes; the loop and inspector check stay constant.

**Alternatives considered**:

- **Backfill into earlier migrations**: would force a renaming /
  re-stamping of every later revision and break prod's `alembic_version`
  pointer. Rejected.
- **Per-dialect raw `IF NOT EXISTS`**: SQLite doesn't support the
  syntax; would require dialect-specific code paths. The inspector
  approach works uniformly on SQLite + Postgres + MySQL.
- **Just delete the columns from `models.py`**: would silently lose
  application semantics (`Manager.is_active`, `Country.is_active` are
  used by admin filtering UIs and by the rating service to skip retired
  managers in future iterations). Rejected.
- **`db.create_all()` on app startup as a safety net**: hides drift
  rather than fixing it; couples startup to schema mutations. Rejected.

**Forward contract**: A new test file
`tests/test_migrations_schema_parity.py` runs in `make test` (and
therefore in the `Quality & Tests` CI job). It builds a fresh SQLite DB
from migrations only, then asserts every column in
`db.metadata.tables` exists in the inspected schema. Any future model
column without a matching migration fails the test with a precise drift
list — *before* it can reach production.

Companion edits made in the same PR for replay safety:

- Removed `is_active` from the `INSERT INTO leagues / managers (...)` clauses
  in the four data migrations
  `c5e7f9a1b2d4` / `d6f8a2b9c1e3` / `e7a9b3d5c2f1` / `f1c8b2e4a9d6`
  (`server_default` from `a3e91f4c7b28` does the right thing).
- Guarded `9a30d278d31d_remove_obsolete_match_model::upgrade()` with
  `inspector.get_table_names()` so it's a no-op on fresh DBs.

## 2026-05-05: Admin-observer guardrail for tandem manager records

**Context**: Per the league owner, `whiplash 92` and `AleX TiiKii` are
sometimes attached to another team's roster purely for *administrative
observation* (Volga Mafiozi 25/26, Team Femida 25/26). The combined pair
must NOT be recorded as a tandem manager — only the active partner gets
the team's playoff achievement. At the same time, those two are also
regular solo participants elsewhere (10 legitimate solo achievements
across L1 and L2 in 21/22 → 24/25), so a blanket exclusion would be
incorrect. The 22/23 L2 `Tandem: Vlad, whiplash 92` is a real exception:
that pair *did* play as a true tandem, owner-confirmed.

The previous L2.1 25/26 data migration (`e7a9b3d5c2f1`, PR #71) handled
the carve-out **inline** (no `Tandem: Don Georgio, whiplash 92` row
inserted). The owner asked for a **system-level** mechanism so this is
enforced automatically for all future seasons rather than per-migration.

**Decision** (Variant B; complements Variant A in PR #71):

1. **Convention, not schema.** No new column on `managers`, no new
   table, no Alembic migration. The existing solo achievements of
   `whiplash 92` / `AleX TiiKii` keep flowing through scoring untouched.
2. **`data/admin_observers.py`** — new module that owns the canonical
   `ADMIN_OBSERVERS` set + helpers (`normalize`, `parse_tandem_members`,
   `tandem_observer_members`, `validate_manager_name`,
   `load_explicit_tandems`, `is_explicit_tandem`). Matching is
   case-insensitive and whitespace-normalised so `Alex Tiikii`,
   `AleX TiiKii`, and `alex   tiikii` all trigger the rule.
3. **`data/seed/explicit_tandems.json`** — flat JSON list of
   owner-sanctioned mixed tandem strings. Currently a single entry:
   `["Tandem: Vlad, whiplash 92"]`. Order of members inside a tandem
   string is irrelevant — comparisons are normalised to a frozenset of
   member names.
4. **Two enforcement points** — `data/seed_service.py::_seed_managers`
   appends to `result.errors` and skips the row;
   `services/admin/views.py::ManagerModelView.on_model_change` raises
   `ValueError` (Flask-Admin surfaces this as a form-level error). A
   third, defence-in-depth check sits in
   `AchievementModelView.on_model_change` so legacy / out-of-band
   inserts can't silently slip an observer-tandem an achievement.
5. **Solo observer rows are unaffected.** The validator short-circuits
   on non-tandem names — `whiplash 92` / `AleX TiiKii` themselves pass
   through, as do all 60 unrelated managers in the seed.

**Consequences**:

- Admins introducing new tandems via Flask-Admin or seed JSON get a
  clear error message pointing them at `data/seed/explicit_tandems.json`
  if a real tandem with an observer needs to be registered.
- Coverage of the new module is 98% (53 unit + integration tests in
  `tests/test_admin_observers.py`).
- No schema change → no production migration to coordinate. Deploying
  this PR is a simple `git pull` + service restart.

## 2026-05-05: Kilocode adapter — auto-detect `.kilo/` vs `.kilocode/`

**Context**: `scripts/install_superpowers.{sh,ps1}` shipped in TIK-57 with
`dispatch_kilocode()` hard-coded to symlink `.kilocode/skills/superpowers`
(the documented Kilocode plugin path). But this repo, like several
projects in the wild, ships an **in-repo Kilocode orchestrator** layout
under `.kilo/`: `kilo.json`, `kilo.jsonc`, and project skills already at
`.kilo/skills/{skill-creator,webapp-testing,grill-me}`. Running
`make superpowers-install --mode=kilocode` here used to create a
*parallel* `.kilocode/` tree that Kilocode never discovers — so on
Kilocode the upstream superpowers skills were silently invisible.

**Decision**:

1. **Auto-detect, don't hard-code.** Both `dispatch_kilocode` (Bash) and
   the `'kilocode'` switch case (PowerShell) now check whether the repo
   already has `.kilo/` (or `.kilo/kilo.json`, `.kilo/kilo.jsonc`). If
   present, the script symlinks `.kilo/skills/superpowers`; otherwise it
   falls back to the canonical `.kilocode/skills/superpowers`.
2. **Both layouts are uninstalled.** `run_uninstall` in `.sh` and `.ps1`
   now removes both `.kilocode/skills/superpowers` and
   `.kilo/skills/superpowers`, so a tear-down doesn't leave dangling
   symlinks if a user toggles platforms or migrates layouts.
3. **The in-repo `.kilo/skills/superpowers → ../../skills/superpowers/skills`
   symlink is committed.** Parallel to the long-existing
   `.agents/skills/superpowers` symlink, this gives Kilocode users in
   *this* repo immediate parity with Devin / Antigravity / OpenCode users
   without having to run the bootstrap script first.
4. **`AGENTS.md` § 7 install matrix and `.superpowersrc`
   `adapters.kilocode` comment** were updated to document the
   auto-detection. The user-facing default in `.superpowersrc` stays
   `.kilocode/skills/superpowers` (the Kilocode-platform-canonical path);
   the inline comment explicitly says the script auto-rewrites to
   `.kilo/skills/superpowers` when `.kilo/` exists.
5. **`Makefile` `setup` target now runs `submodules-init` first** —
   `git submodule update --init --recursive` — so on a fresh clone the
   `skills/superpowers` submodule is populated before any of the adapter
   symlinks (`.agents/skills/superpowers`, `.kilo/skills/superpowers`)
   are dereferenced. README *Быстрый старт* mentions this.

**Rationale**: the legacy `.kilocode/` path was the documented standard
when TIK-57 wrote the bootstrap, but the in-repo orchestrator pattern
(everything under `.kilo/`) is what this project (and the user's wider
Kilocode workflow) actually uses. Both are valid; neither is wrong.
Auto-detection is the only way the bootstrap stays correct without each
project having to override `.superpowersrc::adapters.kilocode` by hand —
and overrides are explicitly disallowed by the file's own header
(*"do not edit by hand"*). The hard-coded path was a latent footgun:
silent miss with no error. Auto-detection trades one branch in 4 lines
of bash for a footgun-free behaviour.

**Status**: Implemented in PR #68 (merged 2026-05-05).
[github](https://github.com/amatjkay/shadow-hockey-league_v2/pull/68).

---

## 2026-05-04: TIK-57 — bootstrap obra/superpowers as a parallel skill layer

**Context**: User requested integration of [`obra/superpowers`](https://github.com/obra/superpowers)
across **Devin.io, Claude Code, OpenCode, Codex CLI/App, Cursor, Copilot CLI,
Gemini CLI, Kilocode, Hermes, and Antigravity**. The repo already has a curated
project-specific skill set under `.agents/skills/<name>/SKILL.md` (7 skills,
codified in AGENTS.md § 3 + `docs/INDEX.md`); upstream Superpowers is a
*methodology-level* skill set (TDD, brainstorming, writing-plans,
subagent-driven-development, …) and should not displace project skills.

**Decision**:

1. **Additive integration (not replacement)**. Project skills under
   `.agents/skills/<name>/SKILL.md` keep precedence. Upstream skills are
   exposed *alongside* via a symlink at `.agents/skills/superpowers/` →
   `skills/superpowers/skills/`. Conflict resolution: project skills win;
   explicit disable list in `.superpowersrc::disabled_skills`.

2. **Single bootstrap with platform detection** (`scripts/install_superpowers.{sh,ps1}`).
   `detect_platform()` runs once and dispatches per platform: native plugin
   commands for Claude Code / Cursor / Codex / Copilot / Gemini (script
   prints, doesn't write), `opencode.json[plugin]` merge for OpenCode,
   submodule + symlink for Devin / Antigravity / Kilocode / unknown,
   submodule + `external_skill_dirs` config snippet for Hermes. Windows uses
   NTFS junctions (no admin needed) instead of POSIX symlinks. Dry-run is
   default (`--apply` required to mutate); `--check` is the pre-commit-friendly
   variant.

3. **Vendoring via git submodule, pinned at upstream tag `v5.0.7`**
   (commit `1f20bef`). Rationale: pinning gives reproducible installs across
   sessions; submodule (vs subtree or runtime fetch) plays well with the
   project's existing CI (no extra fetch step) and respects the
   *«предпочитай symlink/fetch, не копируй файлы»* constraint. Updates via
   `make superpowers-update` (remote fast-forward) or explicit
   `git -C skills/superpowers checkout <tag>` + commit-and-bump
   `.superpowersrc::upstream_ref`.

4. **`active_skills: all` semantic** in `.superpowersrc`. Per the user's
   explicit directive, every upstream skill ships enabled (currently 14:
   brainstorming, dispatching-parallel-agents, executing-plans,
   finishing-a-development-branch, receiving-code-review, requesting-code-review,
   subagent-driven-development, systematic-debugging, test-driven-development,
   using-git-worktrees, using-superpowers, verification-before-completion,
   writing-plans, writing-skills). Disabling specific skills happens via
   `disabled_skills:` (currently empty).

5. **Pre-commit framework introduced** (`.pre-commit-config.yaml` + `pre-commit`
   in `requirements-dev.txt`). Single local hook
   (`superpowers-skills-check`) that calls `scripts/install_superpowers.sh
   --check`. Heavy lifting (`make check`, `make test`, `make audit-deps`)
   stays in CI, where it always ran. Wired in by `make precommit-install`
   (one-shot per checkout).

6. **`AGENTS.md` § 7 added; § 1–6 unchanged.** Per AGENTS.md § 2 file-safety,
   the constitution is touched additively only. Version-history row added in
   § 6 to track this change.

7. **Side-effect: scoped CI exclusions added to `pyproject.toml` and
   `.flake8`** for the four broken root-level stubs (`locustfile.py`,
   `run_performance_test.py`, `test_mcp_client.py`, `test_linear_mcp.py`)
   and the `.kilo/` agent-config tree. These were introduced in commit
   `4339b7b` (direct push to main, 2026-05-04) and have been silently
   breaking `make check` since then; PR #62 merged red. Underlying files
   were left untouched (file-safety + minimal changes); only
   tooling-config exclusions were added, with in-line rationale.

**Rationale**: Methodology-level skills (TDD, plans, subagents) are
genuinely useful and well-curated upstream; reinventing them locally is
wasted effort. Pinning at a tag gives the same reproducibility guarantees as
project skills (which live in-tree). The platform-detection-with-dispatch
pattern matches how the repo already handles Devin/Antigravity vs Kilocode
markers.

**Status**: Implemented; PR open against `main`. CI verification pending.

---

## 2026-05-03: TIK-51 tech-debt continuation — pip-audit, mypy, coverage gate, e2e in CI

**Context**: Post-TIK-42, three latent tech debts remained: (1) `pip-audit` was
not in CI, so dependency CVEs were caught only on demand; (2) `mypy` had been
disabled in CI (TIK-39 was a one-shot cleanup, no enforcement); (3) coverage on
`services/blueprints/app/models` had only reached 84% (target ≥ 87%); (4) the
42-scenario Playwright smoke suite ran only locally — regressions in admin
views or auth boundary could land on `main` undetected.

**Decision**:

1. **pip-audit gate (TIK-52)** — runtime CVEs (`requirements.txt`) fail CI;
   dev-only CVEs (`requirements-dev.txt`) are reported but do not fail. The
   `make audit-deps` target is the single entrypoint; the CI step shells out
   to it. Rationale: dev-only CVEs are common (e.g., test runners, formatters
   with transitive issues) and would create noise without buying production
   safety.
2. **mypy back in `make check` and CI (TIK-53)** — re-enabled with the existing
   `mypy.ini` config; fixed all 40 errors on the source tree; 0 errors today.
   Rationale: type safety is cheap to enforce after the one-shot fix and gives
   refactoring confidence. Where Flask-SQLAlchemy session proxies confused mypy,
   we introduced `services/_types.py::SessionLike` rather than `# type: ignore`.
3. **Coverage to 87% (TIK-54)** — added 49 targeted tests on previously low-cov
   files: Redis socket-timeout error paths in `blueprints/health.py`; admin view
   formatters in `services/admin/views.py`; recalc/metrics corner cases; create-
   app failure modes. Did not chase 100% — pragmatic stop where the remaining
   gaps are init guards and dead-on-startup branches.
4. **E2E Playwright smoke as a separate CI job (TIK-55)** — new
   `E2E Smoke (Playwright)` job in `.github/workflows/deploy.yml`, downstream of
   `quality-and-tests` and upstream of `deploy`. Same script as local
   (`tests/e2e/test_smoke.py`); `scripts/create_e2e_admin.py` provisions the
   `e2e_admin` super-admin idempotently. Rationale for keeping it separate from
   the unit-test job: e2e wants Redis service + browser binaries + a live dev
   server boot, all of which would slow `quality-and-tests` substantially even
   on green runs.

**Rationale**:
- All four debts had been listed in `docs/activeContext.md` as outstanding
  follow-ups. Closing them as a coordinated mini-epic (rather than ad hoc)
  ensured consistent CI shape and a single docs sync.
- Keeping `pip-audit` and `mypy` in the same `quality-and-tests` job rather than
  parallel jobs minimises matrix complexity for a low-traffic repo. If queue
  time becomes an issue we can split later.

**Trade-offs**:
- `pip-audit` adds ~10s to CI; `mypy` adds ~6s; e2e job adds ~90s end-to-end on
  fresh runners. Net CI wall-clock for a typical PR went from ~120s to ~210s.
  Worth it for type/security/UI regression coverage on every PR.
- The schema-bootstrap step (`db.create_all()`) in the e2e CI job duplicates
  what `make init-db` does locally. We accept the duplication because the CI
  flow boots a bare runner where `instance/dev.db` doesn't exist; pulling in
  the full Makefile target would drag dev-only build deps.

**Forward contracts**:
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

## 2026-05-03: TIK-42 cleanup — 3 monolith→package splits, CC reduction, dedup

**Context**: Post-audit (audit-2026-04-28 closed in PRs #41-#46), three Python files
exceeded 600 LOC (`services/api.py` 920, `blueprints/admin_api.py` 893, `services/admin.py`
635), four functions had cyclomatic complexity ≥ D, and `tests/test_rating_service.py`
contained four duplicate test classes. Coverage on services/blueprints/app was 81%.

**Decision**:

1. **Decompose each large file into a package**, not a flat split:
   - Create `<module>/__init__.py` that owns the Flask `Blueprint` (or `init_admin`
     entrypoint) and re-exports the public symbols.
   - Move per-resource handlers (countries / managers / achievements; ModelViews;
     lookups) into sibling submodules.
   - Submodules import the Blueprint from `__init__.py` and register routes via
     decorator. Circular-import safe because the Blueprint is created BEFORE the
     submodule imports inside `__init__.py`.
   - Keep `from services.api import api`, `from blueprints.admin_api import
     admin_api_bp`, `from services.admin import init_admin` working unchanged so
     consumers (chiefly `app.py`) need no edits.
2. **Cap cyclomatic complexity at C** for hot functions; refactor by extracting
   per-branch helpers (e.g. `_validate_one`, `_persist_batch`, `_render_summary`)
   rather than rewriting business logic.
3. **Dedup tests** by removing duplicate `TestAppRoutes`, `TestSecurityHeaders`,
   `TestValidationService`, `TestAPIEndpoints` classes from
   `tests/test_rating_service.py`. The canonical copies live in their topic-named
   files. Rename `tests/test_e2e.py` → `tests/integration/test_smoke_endpoints.py`
   because it uses Flask test client, not Playwright — the previous name lied.
4. **Archive `scratch/` to `scripts/oneoff/`** with a README explaining provenance,
   instead of deleting. One-off prod-sync scripts retain historical reference and
   stay out of agent search via `pyproject.toml` exclusions.
5. **Coverage boost** via targeted error-path tests in `recalc_service` /
   `metrics_service` / `app.py`. Did not chase 100% — pragmatic stop at the
   exception handlers and singleton corner cases.
6. **Stack landing**: PRs #47-#54 stacked into each other instead of main. After the
   user merged them sequentially they all collapsed into PR #55 (the final stack
   head). Resolved 2 conflicts against TIK-43 (#47, which had landed independently)
   by keeping HEAD — the splits already incorporated the canonical cache import.
7. **Verification**: 423 unit/integration tests pass; six-test smoke run on `main`
   covers all 3 split packages via UI (leaderboard, public API, admin login,
   manager list, lookup endpoint).

**Rationale**:
- Package-level decomposition beats flat split because per-resource files become
  navigable and reviewable in isolation, while the `__init__.py` stays the only
  place that knows about cross-resource glue.
- Backward-compat re-exports remove churn: no consumer change in `app.py`, no
  fixture change in tests, no doc change for "where does X live".
- Capping CC at C (not B) keeps reviews short — going below C usually means
  splitting a meaningful business operation across files for cosmetic reasons.

**Trade-offs**:
- More files, deeper directory tree. Mitigated by `docs/INDEX.md` map and the
  `codebase-map` skill.
- Coverage on `app.py` and `recalc_service` still below 87% target. Closing the
  gap fully needs end-to-end fixtures, which were out-of-scope.
- `services/admin/views.py` is still 342 LOC. Splitting per-ModelView file would
  be cosmetic — kept as a single file because all views share the `SHLModelView`
  base patterns and reading them together helps debugging.

**Source**: `docs/progress.md` 2026-05-03 entry; PRs #47-#55; Linear epic TIK-42.

---

