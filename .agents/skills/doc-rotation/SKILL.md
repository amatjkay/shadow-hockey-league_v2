# SKILL: Doc Rotation

## Purpose

Move stale entries from `docs/progress.md` and `docs/decisionLog.md` into quarterly archive files so per-turn reads stay cheap. Move-only — never delete or reword.

## When to Use

- Main file > 200 lines OR > 12 dated entries.
- Triggered manually by `doc-curator` agent.
- Quarterly maintenance (calendar Q-end).

## Tools used (verified 2026-05-05)

This skill uses only tools that are actually present in the current Devin
session. Older versions referenced a `filesystem` MCP server — it was retired
in TIK-57 and replaced by built-in equivalents.

- `read` / `edit` / `write` for `docs/` access (replaces the retired
  `filesystem` MCP).
- `grep` for header indexing.
- `exec` running `sed` / `awk` / `wc` for section extraction and line counts.

## Workflow

### Step 1 — Inventory

```bash
wc -l docs/progress.md docs/decisionLog.md
grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/progress.md
grep -nE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' docs/decisionLog.md
```

### Step 2 — Decide cut-line

- Keep latest **10** dated entries in main file.
- Everything older → `docs/archive/YYYY-QN.md`.
- Undated retrospectives ("Stabilization Phase", "Feature Roadmap") → `docs/archive/legacy-retrospectives.md`.
- If main file < 200 lines AND has < 12 entries → no rotation; exit early.

### Step 3 — Move (preserve verbatim)

For each entry to archive:

1. Identify start/end line via `grep` (`## YYYY-MM-DD …` headers; end = line before next `## ` or EOF).
2. `sed -n 'A,Bp' main.md >> archive.md`.
3. Delete the same range from main file via `sed -i 'A,Bd' main.md`.
4. Insert one-line index reference at the top of main file:
   ```
   > Archive: 2026-Q1 → docs/archive/2026-Q1.md (12 entries 2026-01-04 → 2026-03-30)
   ```

### Step 4 — Index update

Append archive filename to `docs/INDEX.md` with a "when to read" note.

### Step 5 — Verify

```bash
wc -l docs/progress.md docs/decisionLog.md docs/archive/*.md
git diff --stat
```

Commit message format:
```
docs: rotate Memory Bank (saves ~N tokens/turn, progress.md X→Y, decisionLog.md X→Y)
```

## Safety Rules

- **Never** rewrite or summarize archived entries.
- **Never** drop ADR forward-contracts — if an ADR is archived, keep its "Forward contracts" section duplicated as a stub in the main file under `## Active Forward Contracts`.
- If an entry is linked from an open PR or `docs/audits/*`, leave a stub anchor `<a id="2026-04-29-audit-remediation"></a>` at the original line pointing to the archive.

## Rollback

```bash
git revert <rotation_sha>     # entire rotation reverts atomically
```
