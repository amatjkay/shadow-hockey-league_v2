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

## 2026-05-13: TIK-101 / TIK-102 / TIK-103 — `_is_redis_available()` always defaults to localhost:6379, no short-circuit

**Context**: After TIK-100 mitigated the production "season-tab hang" with
deploy-time cache pre-warm, 10/10 `/health` probes still reported
`cache_backend_type=SimpleCache` post-deploy. Three-iteration drill-down
found the root cause was a short-circuit in `_is_redis_available()` that
was never reachable in the test/CI environment but always tripped on prod.

**Decision**: Remove the short-circuit. `_is_redis_available()` now
unconditionally constructs `redis://{REDIS_HOST or localhost}:{REDIS_PORT
or 6379}/{REDIS_DB or 0}` and probes it through the TIK-101 retry loop.
This mirrors the defaults the cache_config block 80 lines later already
uses for `CACHE_REDIS_HOST` / `CACHE_REDIS_PORT` / `CACHE_REDIS_DB`. No
server-side config change required; the production systemd unit's lack of
`REDIS_URL` / `REDIS_HOST` / `REDIS_PORT` env vars is now compatible.

**Forward contract (do not regress)**:

- `_is_redis_available()` **must not** add new short-circuits before the
  retry loop. Specifically, do not re-add the
  `if not redis_url: return False` early-exit. The retry loop
  (`REDIS_INIT_RETRIES`, default 5; 1 in TESTING) is the only correct
  way to declare Redis unavailable.
- `tests/conftest.py::_FakeRedis` **must** implement every redis-py
  method that `flask_caching.backends.rediscache.RedisCache` and
  `services.cache_service.invalidate_leaderboard_cache()` call. Currently
  this is: `get`, `set`, `setex`, `getset`, `delete`, `mget`, `keys`,
  `scan_iter`, `ping`, `info`, `expire`, `ttl`, `exists`, `flushdb`,
  `pipeline`, `execute`. If you exercise a new RedisCache code path,
  extend the fake or tests will silently mask the bug (TIK-102 added
  `scan_iter` after CI surfaced this).
- `/health` endpoint **must** expose `cache_backend_type` and
  `cache_type_config` so post-deploy validation (`curl /health × 10`)
  remains a reliable smoke test for cache wiring. Do not remove the
  TIK-100 instrumentation.

**Diagnostic playbook (for future cache regressions)**:

1. `curl https://shadow-hockey-league.ru/health × 10` and verify
   `cache_backend_type=RedisCache` on all 10 probes (catches all 4
   round-robined workers).
2. If any probe shows `SimpleCache`, check the worker's systemd journal
   for the INFO log
   `"REDIS_URL not set; defaulting to redis://localhost:6379/0 ..."` —
   absence indicates the new fallback branch isn't engaging; presence
   plus SimpleCache indicates the retry exhausted (Redis genuinely
   unreachable).
3. `redis-cli ping` on the host to confirm Redis is up. Never trust
   `/health.redis_status` for cache wiring — it can read `connected`
   while workers run SimpleCache (different code path,
   `CACHE_REDIS_HOST` defaults to localhost).

**Related**: TIK-100 (deploy.sh warmup + /health instrumentation — kept
as belt-and-suspenders), TIK-86 (`_LEADERBOARD_LOCK`, unrelated to this).

---

## 2026-05-13: TIK-96 — prefix invalidation for `leaderboard*` keys (replaces `cache.clear()`)

**Context**: `services/cache_service.invalidate_leaderboard_cache()` used to
call `cache.clear()` on every manager/achievement/country CRUD. That
flushed **all** keys in the configured backend — including
Flask-Limiter rate-limiter counters when they share the same Redis
instance (`RATELIMIT_STORAGE_URI` defaults to the cache URL in
`app.py`). The cache-key contract owned by
`blueprints/main.py::_leaderboard_cache_key` is narrow — `leaderboard`
and `leaderboard:{season_id}` — so a full `flushdb` was always
over-broad. Surface today is small; left in place it would scale into
a real cost as more cached namespaces land.

**Options Considered**:

1. **Keep `cache.clear()` (status quo).** Simplest. Continues to wipe
   unrelated keys (rate-limit counters, future cached namespaces).
   Rejected — already known to be over-broad.
2. **Maintain a side index of leaderboard keys in a Redis set
   (`SADD leaderboard:_index` on write, `SMEMBERS + DEL + DEL index`
   on invalidate).** Tightest semantics, no SCAN cost, but requires
   intercepting every cache write (we'd need to override
   `@cache.cached` or wrap `cache.set`). Rejected as overkill for
   one view with at most 6 keys (`leaderboard` + 5 seasons).
3. **`SCAN` over `{CACHE_KEY_PREFIX}leaderboard*` and `DELETE`
   matched keys (Redis); iterate `_cache.keys()` and `cache.delete`
   matching keys (SimpleCache); fall back to `cache.clear()` for
   unknown backends with a warning.** Targets the exact prefix the
   view writes, costs O(matches) on Redis via cursor-paged SCAN,
   leaves unrelated keys alone. Chosen.
4. **Drop the `cache.clear()` fallback for unknown backends.**
   Considered. Rejected — silently retaining stale entries on a
   custom backend would re-introduce the bug we just fixed in a
   different shape. A logged `cache.clear()` is the safe default
   when the backend type is unrecognised.

**Decision**: Option 3.

- `cache.cache._write_client.scan_iter(match=f"{key_prefix}leaderboard*")`
  for `RedisCache` (`key_prefix` is whatever `cachelib` stored from
  `CACHE_KEY_PREFIX`; defaults to `""`).
- `cache.cache._cache.keys()` + `cache.delete(key)` for `SimpleCache`
  (the test/dev backend).
- `logger.warning(...)` + `cache.clear()` for anything else.

**Reversibility**: Pure swap-out of the function body. To revert,
restore the `cache.clear()` one-liner — no schema migration, no
contract change. The cache-key contract in `_leaderboard_cache_key` is
explicitly out of scope (TIK-96 § anti-goals).

**Regression coverage**:
`tests/integration/test_cache_invalidation.py::TestPrefixInvalidation::test_prefix_invalidation_preserves_unrelated_keys`
warms `/`, sets an `unrelated_key`, calls
`invalidate_leaderboard_cache()`, and asserts the `leaderboard` key
is gone while `unrelated_key` survives. Runs on the
`SimpleCache`-backed `TestingConfig`; the conftest-level FakeRedis
patch covers the Redis branch transitively when env config promotes
the backend.

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

## ADR-006: Rebalanced Achievement Points — Consistent 2:1 L1:L2

**Date:** 2026-06-11
**Status:** Active

### Context

The original point values (ADR-004 era) had several design inconsistencies:

1. **L1:L2 ratio varied wildly** — from 1.25× (BEST: 50/40) to 4.5× (TOP3:
   450/100) with no logical rationale for which achievement deserved a wider
   gap.
2. **TOP1:R1 gap was 80:1** (800 vs 10) — a manager could participate in
   every playoff for 20 years and accumulate only 200 points, a quarter of
   one championship. Career consistency was nearly meaningless.
3. **BEST (50) severely under-valued** — winning the regular season was worth
   only 1.6× a single playoff-round win (R3: 30).
4. **R3 (30) vs R1 (10) gave only 3×** for advancing two rounds, yet R3 vs
   TOP3 (450) was a 15× chasm — progression curve deeply uneven.

### Decision

Redesign the point system around three principles:

**Principle 1 — Consistent 2:1 L1:L2.** Every achievement type in League 2
is worth exactly half of League 1. No exceptions.

**Principle 2 — Playoff progression ≈ 2× per round won.** Each successive
playoff round approximately doubles in value.

**Principle 3 — Regular season ≈ semifinal.** BEST (regular-season champion)
is pegged to 200 — comparable to R3 (150) but clearly above it.

| Code | L1 | L2 | L1:L2 | Rationale |
|:-----|:--:|:--:|:-----:|:----------|
| TOP1 | 1000 | 500 | 2:1 | Champion — crown achievement |
| TOP2 | 600 | 300 | 2:1 | Finalist — 60 % of champion |
| TOP3 | 400 | 200 | 2:1 | Semifinalist — 2.67× R3 |
| BEST | 200 | 100 | 2:1 | Regular-season champion |
| R3 | 150 | 75 | 2:1 | Quarterfinal winner — 2× R1 |
| R1 | 80 | 40 | 2:1 | Playoff participant |

Key ratios in the new system:
- **TOP1 : R1 = 12.5:1** (was 80:1) — ≈13 seasons of playoff presence
  equals one championship; realistic career curve.
- **TOP1 : BEST = 5:1** (was 16:1) — regular season is meaningful but
  a title is clearly superior.
- **TOP1 : TOP3 = 2.5:1** — champion worth 2.5× a semifinalist.
- **R3 : R1 ≈ 1.9:1** — consistent progression.

### Consequences

- All existing achievements need recalculation (handled by migration
  `d4e5f6a7b8c9`).
- Tooltip and points-info strip reflect the new values.
- Seed migration `b2c3d4e5f6a7` updated with new defaults for fresh
  installs.
- L2 values are now exactly half of L1; separate `base_points_l1` /
  `base_points_l2` columns are retained for future flexibility.

