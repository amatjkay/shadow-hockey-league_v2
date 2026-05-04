# Superpowers Skill Bridge

> Bridge between this repo and the upstream
> [obra/superpowers](https://github.com/obra/superpowers) skill set.
> Source of truth: [`.superpowersrc`](../.superpowersrc).
> Bootstrap: [`scripts/install_superpowers.sh`](../scripts/install_superpowers.sh)
> (POSIX) and [`scripts/install_superpowers.ps1`](../scripts/install_superpowers.ps1) (Windows).
> See [`AGENTS.md` § 7](../AGENTS.md#7-superpowers-skill-bridge-since-2026-05-04)
> for the contract.

## TL;DR

```bash
# 1. Detect platform and print what would happen (dry-run).
scripts/install_superpowers.sh

# 2. Actually install (initializes the submodule, creates the symlink/junction).
scripts/install_superpowers.sh --apply

# 3. Optional: validate config + submodule from CI / pre-commit.
scripts/install_superpowers.sh --check

# 4. Tear it all down.
scripts/install_superpowers.sh --uninstall --apply
```

`make superpowers-install`, `make superpowers-status`, and
`make superpowers-update` are convenience wrappers.

## Per-platform install

The bootstrap script auto-detects the platform; the table below shows what
each detection branch does. Pass `--mode=<platform>` to override.

| Platform | Detection | Action | Modifies repo? |
| --- | --- | --- | --- |
| **Claude Code** | `which claude` | Prints `/plugin install superpowers@claude-plugins-official` (run inside Claude Code) | no |
| **Cursor** | `~/.cursor/` or `$CURSOR_TRACE_ID` | Prints `/add-plugin superpowers` (run in Cursor Agent chat) | no |
| **Codex CLI** | `which codex` | Prints `/plugins` → search `superpowers` → Install | no |
| **Codex App** | (manual `--mode=codex-app`) | Prints sidebar walkthrough | no |
| **OpenCode** | `which opencode` or `opencode.json` exists | Adds `"superpowers@git+https://github.com/obra/superpowers.git"` to `opencode.json[plugin]` (idempotent, requires `jq`) | yes (`opencode.json`) |
| **Copilot CLI** | `which copilot` | Prints `copilot plugin marketplace add … && copilot plugin install …` | no |
| **Gemini CLI** | `which gemini` | Prints `gemini extensions install https://github.com/obra/superpowers` | no |
| **Kilocode** | `~/.kilocode/`, `.kilocode/kilo.json`, or `.kilo/kilo.json` | Initializes `skills/superpowers` submodule, creates symlink (Linux/macOS) or junction (Windows) at `.kilocode/skills/superpowers/` → `skills/superpowers/skills/` | yes (`.gitmodules`, symlink) |
| **Hermes** | `~/.hermes/` or `$HERMES_HOME` | Initializes submodule, prints the `external_skill_dirs` snippet to add to `~/.hermes/config.toml` | yes (submodule), no (Hermes config is user-global) |
| **Antigravity** | `.antigravityrules` exists, no other markers | Initializes submodule, symlinks `.agents/skills/superpowers/` | yes |
| **Devin.io** | `$DEVIN_USER` or `$DEVIN_RUN` | Initializes submodule, symlinks `.agents/skills/superpowers/`. AGENTS.md § 7 already declares this path as a skill-discovery location. | yes |
| **unknown** | none of the above | Falls back to the Devin/Antigravity behavior with a warning | yes |

## Native install commands (copy-paste)

For platforms where the script just prints guidance:

```text
# Claude Code (Anthropic Marketplace)
/plugin install superpowers@claude-plugins-official

# Claude Code (obra Marketplace)
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# Cursor
/add-plugin superpowers

# OpenAI Codex CLI
/plugins
superpowers
→ Install Plugin

# GitHub Copilot CLI
copilot plugin marketplace add obra/superpowers-marketplace
copilot plugin install superpowers@superpowers-marketplace

# Gemini CLI
gemini extensions install https://github.com/obra/superpowers
gemini extensions update superpowers   # to bump
```

## Verifying

| What to check | How |
| --- | --- |
| Bootstrap is wired | `make superpowers-status` |
| Submodule is on the pinned ref | `git -C skills/superpowers describe --tags` → `v5.0.7` |
| Adapter symlink resolves | `readlink .agents/skills/superpowers` (or `Get-Item …` on Windows) |
| Skills discoverable | `ls .agents/skills/superpowers` (Devin/Antigravity), or `ls .kilocode/skills/superpowers` (Kilocode) |
| Native plugin alive (Claude Code / Cursor / Codex / Copilot / Gemini) | `/superpowers status` (slash command), or platform-equivalent |
| Pre-commit hooks fire | `git commit --allow-empty -m 'sanity'` after `make precommit-install` |

## Conflict resolution with project skills

Project-specific skills in `.agents/skills/<name>/SKILL.md` always take
precedence over upstream Superpowers skills with the same name (none
currently overlap). To explicitly disable an upstream skill, add it to
`disabled_skills` in [`.superpowersrc`](../.superpowersrc).

## Updating the upstream pin

```bash
make superpowers-update          # git submodule update --remote skills/superpowers
git -C skills/superpowers checkout v5.1.0   # or any tag/sha
git add skills/superpowers .superpowersrc   # also bump upstream_ref:
git commit -m "chore(superpowers): bump to v5.1.0"
```

## Fallbacks

| Scenario | Workaround |
| --- | --- |
| `git submodule add` blocked by policy | Use `git subtree add --prefix=skills/superpowers --squash https://github.com/obra/superpowers v5.0.7`. The script's `--check` accepts either. |
| Submodule fetch unreachable from VM | Set `SUPERPOWERS_TARBALL_URL=<https://...tar.gz>` and run `--apply`; the script will `curl | tar xz` instead. |
| Kilocode does not pick up the symlink ([Kilo-Org/kilocode#5408](https://github.com/Kilo-Org/kilocode/issues/5408)) | Pass `--copy-instead-of-link` (planned follow-up). For now: `cp -r skills/superpowers/skills/* .kilocode/skills/superpowers/` after `--apply`. |
| Hermes does not honour `external_skill_dirs` | Symlink `~/.hermes/skills/superpowers → $PWD/skills/superpowers/skills`. |
| Pre-commit framework not allowed | Skip `make precommit-install`; the project's CI gates (`make check`, `make test`, `make audit-deps`) still cover the same checks. The local hooks are convenience-only. |

## Uninstall

```bash
scripts/install_superpowers.sh --uninstall --apply
```

This deinitializes the submodule, removes the per-platform symlink/junction,
and leaves `.superpowersrc` and AGENTS.md § 7 untouched (re-running
`--apply` will restore the install).
