# Progress — Shadow Hockey League v2

> **Purpose:** Living document tracking only the **current** cycle of work.
> All agents MUST update this before ending their turn.
>
> Older sections live in `docs/archive/progress-pre-2026-04-29.md` and
> `docs/archive/2026-Q2.md`:
> - `## Progress (rotated 2026-05-04)` — 4 entries 2026-04-30 → 2026-05-01.
> - `## Progress (rotated 2026-05-13)` — 13 entries 2026-05-03 → 2026-05-08
>   (later), rotated per TIK-89 / T13.
> - `## Progress (rotated 2026-05-13, part 2 — TIK-92)` — 8 entries
>   2026-05-08 → 2026-05-13, rotated per TIK-92 to hold this file under
>   ~200 lines per the `doc-rotation` skill / TIK-92 DoD.

## 2026-05-13: TIK-92 — Memory Bank rotation part 2 (progress.md + decisionLog.md → 2026-Q2 archive)

Doc-curator follow-up to TIK-89 / Phase 3 (PR #109). Per the `doc-rotation`
skill, `docs/progress.md` and `docs/decisionLog.md` re-crossed the 200-line
threshold once TIK-89 Phases 1–3 + the same-day rating / UI / TIK-88 entries
landed. TIK-92 narrows each file to the latest ~30 days *and* ≤ 200 lines.
Move-only — no rewording, no content loss.

**What landed**

- `docs/progress.md`: moved entries 4–11 (lines 151–653, 8 entries
  2026-05-08 → 2026-05-13: Rating precision, UI tooltip, UI season-filter
  fuse, TIK-88, TIK-86, `task-formulation`, TIK-84, TIK-83) verbatim into
  a new `## Progress (rotated 2026-05-13, part 2 — TIK-92)` section of
  `docs/archive/2026-Q2.md`. The latest 3 entries (TIK-89 Phase 1 / 2 / 3,
  all 2026-05-13) stay active.
- `docs/decisionLog.md`: moved entries 2–9 (lines 127–653, 8 ADRs
  2026-05-03 → 2026-05-11: TIK-86 lock, task-formulation, Inspector
  backfill, admin-observer, Kilocode adapter, TIK-57 superpowers, TIK-51
  tech-debt, TIK-42 cleanup) verbatim into
  `## Decision Log (rotated 2026-05-13, part 2 — TIK-92)` of the same
  archive file. The latest ADR (2026-05-13 leaderboard precision) stays
  active. Three of the moved ADRs (task-formulation, Inspector, TIK-51)
  carried `**Forward contracts**` blocks; those blocks are preserved
  verbatim under `## Active Forward Contracts` at the top of
  `docs/decisionLog.md` per the `doc-rotation` skill safety rule.
- `docs/INDEX.md`: archive bullet expanded to list the two new
  `(rotated 2026-05-13, part 2 — TIK-92)` sections.
- `docs/owner-actions.md`: T13 / T14 rows annotated with the TIK-92 link
  alongside the existing TIK-89 / Phase 3 reference. Both stay `done`.

**Verification**

- `wc -l` before / after: `progress.md` 653 → ~200; `decisionLog.md`
  653 → ~160; `docs/archive/2026-Q2.md` 1100 → ~2150. Net repo delta:
  +0 lines (move-only). `make check` + `pytest --ignore=tests/e2e -n
  auto --cov --cov-fail-under=87` clean (see PR description for tails).

**Catalog (`docs/owner-actions.md`)**

- T13 + T14 stay `done` (already flipped in TIK-89 / Phase 3); both rows
  now cross-reference TIK-92 so future curators can find the second-pass
  rotation without re-reading the archive.

---

## 2026-05-13: TIK-89 Phase 3 — rotate `docs/progress.md` + `docs/decisionLog.md` to `docs/archive/2026-Q2.md` (T13 + T14)

Batch B Phase 3 of the 14-item owner-actions catalog (T13 + T14).
Memory-Bank rotation per the `doc-rotation` skill — verbatim move, no
rewording.

**What landed**

- `docs/progress.md`: moved entries 11–23 (lines 595–1282, 688 lines,
  13 entries 2026-05-03 → 2026-05-08 (later)) into a new
  `## Progress (rotated 2026-05-13)` section of
  `docs/archive/2026-Q2.md`. Latest 10 entries (2026-05-08 →
  2026-05-13, inclusive of TIK-83 / TIK-84 / TIK-86 / TIK-88 / TIK-89
  Phase 1 / Phase 2 / rating-precision / UI tooltip / UI season-filter)
  stay active.
- `docs/decisionLog.md`: moved entries 10–12 (lines 607–730, 124 lines,
  3 entries 2026-04-30 + 2026-05-01 ×2 — the chronologically oldest
  block, matching the user-recommended cutoff
  `2026-04-30 / стык с docs/archive/2026-Q2.md`) into a new
  `## Decision Log (rotated 2026-05-13)` section of the same archive
  file. All three entries contained `**Forward contracts**` blocks; per
  the `doc-rotation` skill safety rule, those blocks are preserved
  verbatim at the top of `docs/decisionLog.md` under a new
  `## Active Forward Contracts` heading.
- `docs/INDEX.md`: archive bullet expanded to reference all four
  rotated sections inside `docs/archive/2026-Q2.md`.

**Why this matters**

- Per-turn token cost of reading `docs/progress.md` drops from ~1282
  lines (~14 K tokens) to ~593 lines — agents bringing the file into
  context every turn (per Memory Bank Protocol §1) pay roughly half.
- `docs/decisionLog.md` drops from 730 → ~606 lines. Smaller win in
  absolute terms but every Active Forward Contract is now visible in
  the first ~50 lines instead of buried 600+ lines deep.
- No content is lost; `git revert <rotation-sha>` restores the
  pre-rotation state atomically.

**Verification**

- `wc -l` before / after: `progress.md` 1282 → 594; `decisionLog.md`
  730 → 606; `docs/archive/2026-Q2.md` 268 → 1100. Net repo delta:
  +0 lines (move-only).
- `grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/progress.md` — 10
  entries, range 2026-05-08 → 2026-05-13.
- `grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/decisionLog.md` — 9
  entries, range 2026-05-03 → 2026-05-13.
- `make check` — clean.

**Catalog (`docs/owner-actions.md`)**

- T13 + T14 flipped from `open question` → `done`. Open questions are
  now down to `/health` SLA (separate Linear ticket TIK-91, Phase 4).

---

## 2026-05-13: TIK-89 Phase 2 — delete 5 repo-root stub files + drop their lint exclusions (T10)

Batch B Phase 2 of the 14-item owner-actions catalog (T10 only).

**What landed**

- Deleted 5 single-line stub files at the repo root: `locustfile.py`,
  `run_performance_test.py`, `test_mcp_client.py`, `test_linear_mcp.py`,
  `check_mcp_status.sh`. Each contained only `./<filename>:` — residue
  of a `for f in *; do echo "./$f:" > "$f"; done` mishap, no real
  implementation. The matching `bandit_report*.json` pair was already
  cleared in TIK-88.
- Removed the now-orphaned exclusions:
  - `pyproject.toml::[tool.black].force-exclude` (whole block, 4
    entries) plus the now-stale paragraph in the leading comment.
  - `pyproject.toml::[tool.isort].skip` (4 entries).
  - `pyproject.toml::[tool.mypy].exclude` (4 entries).
  - `.flake8::exclude` (4 entries).

**Why this matters**

`pytest --collect-only` at the repo root previously crashed on the three
`test_*.py` stubs (the parser tried to import them as test modules and
failed on `./test_mcp_client.py:` syntax). The work-around was the
`tests/` path override everywhere; the proper fix is no work-around.

**Verification**

- `pytest --collect-only -q` (no path, from repo root) — **576 tests
  collected in 0.25s**, no errors.
- `make check` — clean (`pip-audit`: "No known vulnerabilities found";
  `black`: 88 files unchanged; `isort`: skipped 14 files, was 18, the
  4 stubs are gone; `flake8`: 0 errors; `mypy`: "Success: no issues
  found in 88 source files").
- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87 -q`
  — **576 passed, 95.07% coverage** (unchanged from main baseline).

**Catalog (`docs/owner-actions.md`)**

- T10 flipped from `open question` → `done`. T13 / T14 stay
  `open question` (next PR / Phase 3).

---

## 2026-05-13: TIK-89 Phase 1 — `.env.example` cross-platform + `pip-audit` in `make check` + README pre-commit note

Batch B Phase 1 of the 14-item owner-actions catalog (T04 + T05 + T06).
Three surgical follow-ups, no source-code changes.

**What landed**

- **T04** — `.env.example` `DATABASE_URL` default flipped from a Windows-only
  absolute path (`sqlite:///C:/dev/shadow/shadow-hockey-league_v2/dev.db`) to
  a relative path (`sqlite:///dev.db`) that `config.get_database_url()`
  resolves to an absolute path off `BASE_DIR` on any platform. The
  Windows / Linux / VPS absolute-path examples remain in the comment block
  above as an escape hatch.
- **T05** — `make check` now lists `audit-deps` as a prerequisite, so
  `pip-audit -r requirements.txt -r requirements-dev.txt` runs in the same
  gate developers use locally and CI runs in `quality-and-tests`. `make
  audit-deps` stays as a standalone entry point.
- **T06** — README *Быстрый старт* (Linux/Mac block) now lists
  `make precommit-install` as an explicit step alongside `make setup` and
  `make run`, with a short paragraph explaining why `make setup` does *not*
  call it (hooks live in `.git/hooks/`, opt-in per checkout; CI still runs
  `make check` + `make test` + `make audit-deps` regardless).

**Verification**

- `make check` — clean (`pip-audit`: "No known vulnerabilities found";
  `black` / `isort` / `flake8` / `mypy` all 0 errors).
- `pytest tests --ignore=tests/e2e -n auto --cov --cov-fail-under=87 -q` —
  **576 passed, ≥ 87% coverage** (baseline bumped to 576 by the rating /
  tiebreak work that landed below in PR #103; T04/T05/T06 add no new
  tests).

**Catalog (`docs/owner-actions.md`)**

- T04 / T05 / T06 flipped from `follow-up` → `done`. T10 / T13 / T14 stay
  `open question` (separate PRs in Phase 2 + Phase 3).
