# Wiki — read this first

This directory is an **Obsidian-compatible vault** that gives a graph view
over the project. Notes here are thin: each one explains a slice of the
system in 5–15 lines, then `[[wikilinks]]` to other notes in this vault
and to canonical docs/code in the parent repo.

## Why a separate vault?

- The repo already has long, authoritative docs (`AGENTS.md`,
  `PROJECT_KNOWLEDGE.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, …)
  whose content lives in *one* place. This vault does **not** duplicate
  them — it cross-references them so a reader can navigate the project
  by topic without grep'ing every directory.
- Obsidian's graph view + wikilinks make the relationship between
  *business rules ↔ services ↔ blueprints ↔ tests* visible at a glance.

## Open it in Obsidian

1. Install [Obsidian](https://obsidian.md/) (free).
2. *File → Open Vault → Open folder as vault…* → pick this directory
   (`docs/wiki/`).
3. Obsidian will create a hidden `.obsidian/` config folder on first
   open. That folder is **git-ignored** at the repo root
   (`docs/wiki/.obsidian/`); do not commit it.
4. Open [[Home]] to start.

## Conventions

- **One topic per note.** If a note grows past ~60 lines, split it.
- **Don't duplicate canonical docs.** Summarise in 5–15 lines, then link.
- **Wikilinks for vault notes** (`[[Architecture]]`), **markdown links
  for outside-vault references** (`[../ARCHITECTURE.md](../ARCHITECTURE.md)`,
  `[app.py](../../app.py)`).
- **Filenames use plain spaces** (Obsidian-friendly), e.g.
  `Scoring & Rating.md`.

## Entry points

- [[Home]] — index of the vault.
- [[Architecture]] — the big picture.
- [[Agents and Skills]] — how AI agents are organised.
- [[Business Rules]] — point formula, baselines.
