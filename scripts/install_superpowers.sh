#!/usr/bin/env bash
# scripts/install_superpowers.sh
# Bootstrap obra/superpowers across supported agent platforms (Claude Code,
# Cursor, Codex CLI/App, OpenCode, Copilot CLI, Gemini, Kilocode, Hermes,
# Antigravity, Devin.io, unknown).
#
# Usage:
#   scripts/install_superpowers.sh                   # dry-run, prints actions
#   scripts/install_superpowers.sh --apply           # actually mutate files
#   scripts/install_superpowers.sh --check           # exit 0 if config valid,
#                                                    #        non-zero otherwise
#   scripts/install_superpowers.sh --uninstall --apply
#                                                    # remove submodule + symlinks
#   scripts/install_superpowers.sh --mode=<platform> # override detection
#   scripts/install_superpowers.sh --upstream-ref=v5.0.7
#
# Source of truth: ../.superpowersrc (read by this script and the upstream
# framework). The script never writes to AGENTS.md, models.py, app.py, or
# config.py (AGENTS.md § 2 file-safety guardrails).
set -euo pipefail

SP_RC="${SP_RC:-.superpowersrc}"
SUBMODULE_PATH_DEFAULT="skills/superpowers"
APPLY=0
CHECK=0
UNINSTALL=0
MODE_OVERRIDE=""
UPSTREAM_REF_OVERRIDE=""

usage() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --check) CHECK=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --mode=*) MODE_OVERRIDE="${arg#--mode=}" ;;
    --upstream-ref=*) UPSTREAM_REF_OVERRIDE="${arg#--upstream-ref=}" ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $arg" >&2; exit 64 ;;
  esac
done

log() { printf '[superpowers] %s\n' "$*"; }
warn() { printf '[superpowers] WARN: %s\n' "$*" >&2; }
die() { printf '[superpowers] ERROR: %s\n' "$*" >&2; exit 1; }

# ----------------------------------------------------------------------------
# .superpowersrc parsing (lightweight; no jq/yq dependency).
# ----------------------------------------------------------------------------

rc_get() {
  # rc_get <key>: prints the scalar value for top-level <key> in $SP_RC.
  local key="$1"
  [[ -f "$SP_RC" ]] || { echo ""; return; }
  awk -v k="$key" '
    $0 ~ "^"k":" {
      sub("^[^:]+:[ \t]*","");
      sub("[ \t]*#.*$","");
      print; exit
    }
  ' "$SP_RC"
}

UPSTREAM=$(rc_get upstream)
UPSTREAM=${UPSTREAM:-https://github.com/obra/superpowers}
UPSTREAM_REF=${UPSTREAM_REF_OVERRIDE:-$(rc_get upstream_ref)}
UPSTREAM_REF=${UPSTREAM_REF:-v5.0.7}
SUBMODULE_PATH=$(rc_get fallback_path)
SUBMODULE_PATH=${SUBMODULE_PATH:-$SUBMODULE_PATH_DEFAULT}

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

do_or_say() {
  if [[ "$APPLY" -eq 1 ]]; then
    log "RUN: $*"
    "$@"
  else
    log "DRY: $*"
  fi
}

require_apply() {
  if [[ "$APPLY" -ne 1 ]]; then
    log "(re-run with --apply to actually perform the action)"
  fi
}

# ----------------------------------------------------------------------------
# platform detection
# ----------------------------------------------------------------------------

detect_platform() {
  if [[ -n "$MODE_OVERRIDE" ]]; then echo "$MODE_OVERRIDE"; return; fi
  if command -v claude     >/dev/null 2>&1; then echo claudecode; return; fi
  if [[ -n "${CURSOR_TRACE_ID:-}" || -d "$HOME/.cursor" ]]; then echo cursor; return; fi
  if command -v codex      >/dev/null 2>&1; then echo codex-cli; return; fi
  if command -v opencode   >/dev/null 2>&1 || [[ -f opencode.json ]]; then echo opencode; return; fi
  if command -v copilot    >/dev/null 2>&1; then echo copilot-cli; return; fi
  if command -v gemini     >/dev/null 2>&1; then echo gemini; return; fi
  # Devin is checked before kilocode/antigravity because a Devin VM may host a
  # repo that *also* declares .kilo/ and .antigravityrules artifacts.
  if [[ -d /opt/.devin || -n "${DEVIN_USER:-}${DEVIN_RUN:-}${__COG_SHELL_INTEGRATION_SCRIPT:-}" ]]; then echo devin; return; fi
  if [[ -d "$HOME/.kilocode" || -f .kilocode/kilo.json || -f .kilo/kilo.json ]]; then echo kilocode; return; fi
  if [[ -d "$HOME/.hermes" || -n "${HERMES_HOME:-}" ]]; then echo hermes; return; fi
  if [[ -f .antigravityrules ]]; then echo antigravity; return; fi
  echo unknown
}

# ----------------------------------------------------------------------------
# submodule / fetch
# ----------------------------------------------------------------------------

submodule_present() {
  [[ -f "$SUBMODULE_PATH/.git" || -d "$SUBMODULE_PATH/.git" ]]
}

ensure_submodule() {
  if submodule_present; then
    log "submodule already present at $SUBMODULE_PATH"
    return
  fi
  if [[ "$APPLY" -ne 1 ]]; then
    log "DRY: git submodule add $UPSTREAM $SUBMODULE_PATH (pin: $UPSTREAM_REF)"
    return
  fi
  log "RUN: git submodule add $UPSTREAM $SUBMODULE_PATH"
  git submodule add "$UPSTREAM" "$SUBMODULE_PATH"
  log "RUN: pin to $UPSTREAM_REF"
  ( cd "$SUBMODULE_PATH" && git fetch --depth=1 origin "tag" "$UPSTREAM_REF" 2>/dev/null || git fetch origin "$UPSTREAM_REF" )
  ( cd "$SUBMODULE_PATH" && git checkout "$UPSTREAM_REF" )
  git add .gitmodules "$SUBMODULE_PATH"
}

remove_submodule() {
  if ! submodule_present; then
    log "submodule already absent"
    return
  fi
  do_or_say git submodule deinit -f "$SUBMODULE_PATH"
  do_or_say git rm -f "$SUBMODULE_PATH"
  do_or_say rm -rf ".git/modules/$SUBMODULE_PATH"
}

# ----------------------------------------------------------------------------
# adapter linking (POSIX symlinks)
# ----------------------------------------------------------------------------

ln_to_skills() {
  # ln_to_skills <target_path>
  # Creates a symlink at <target_path> pointing into the submodule's skills/.
  local target="$1"
  local relative_target

  mkdir -p "$(dirname "$target")"
  if [[ -L "$target" ]]; then
    log "symlink already present: $target"
    return
  fi
  if [[ -e "$target" ]]; then
    warn "$target exists and is not a symlink — skipping (move it aside first)"
    return
  fi
  # Number of "../" segments: count slashes in $target (each level up).
  relative_target=$(python3 - <<PY
import os
target=os.path.normpath("$target")
src=os.path.normpath("$SUBMODULE_PATH/skills")
print(os.path.relpath(src, os.path.dirname(target)))
PY
)
  do_or_say ln -s "$relative_target" "$target"
}

unlink_adapter() {
  local target="$1"
  if [[ -L "$target" ]]; then
    do_or_say rm -f "$target"
  fi
}

# ----------------------------------------------------------------------------
# per-platform dispatchers
# ----------------------------------------------------------------------------

dispatch_native() {
  local p="$1"
  case "$p" in
    claudecode)
      log "Claude Code: marketplace install"
      log "  /plugin install superpowers@claude-plugins-official"
      log "  (alternative) /plugin marketplace add obra/superpowers-marketplace"
      log "                /plugin install superpowers@superpowers-marketplace"
      ;;
    cursor)
      log "Cursor Agent chat: /add-plugin superpowers"
      ;;
    codex-cli)
      log "Codex CLI:"
      log "  /plugins"
      log "  superpowers"
      log "  → Install Plugin"
      ;;
    copilot-cli)
      log "Copilot CLI:"
      log "  copilot plugin marketplace add obra/superpowers-marketplace"
      log "  copilot plugin install superpowers@superpowers-marketplace"
      ;;
    gemini)
      log "Gemini CLI:"
      log "  gemini extensions install $UPSTREAM"
      log "  gemini extensions update superpowers   # to bump"
      ;;
  esac
  log "Native install does not modify the repo."
}

dispatch_opencode() {
  local f="opencode.json"
  if [[ ! -f "$f" ]]; then
    do_or_say bash -c "printf '%s\n' '{ \"plugin\": [] }' >'$f'"
  fi
  if command -v jq >/dev/null 2>&1; then
    if [[ "$APPLY" -eq 1 ]]; then
      log "RUN: merge superpowers plugin into $f"
      tmp=$(mktemp)
      jq '.plugin = ((.plugin // []) + ["superpowers@git+https://github.com/obra/superpowers.git"] | unique)' "$f" >"$tmp"
      mv "$tmp" "$f"
    else
      log "DRY: jq merge → $f"
    fi
  else
    warn "jq not installed — add the following entry to opencode.json[plugin] manually:"
    warn '  "superpowers@git+https://github.com/obra/superpowers.git"'
  fi
}

dispatch_hermes() {
  ensure_submodule
  log "Hermes external skill dir setup:"
  log "  Add to ~/.hermes/config.toml:"
  log "    [skills]"
  log "    external_skill_dirs = [\"\$PWD/$SUBMODULE_PATH/skills\"]"
  log "  …or symlink \$HOME/.hermes/skills/superpowers → $SUBMODULE_PATH/skills"
}

dispatch_kilocode() {
  ensure_submodule
  # Two layouts coexist in the wild:
  #   - .kilocode/skills/  — the documented Kilocode plugin path
  #   - .kilo/skills/      — the in-repo orchestrator layout some projects
  #                          ship (kilo.json + kilo.jsonc + project skills).
  # Prefer the layout already present so we don't create a parallel,
  # never-discovered .kilocode/ tree next to an existing .kilo/.
  local target=".kilocode/skills/superpowers"
  if [[ -d ".kilo" || -f ".kilo/kilo.json" || -f ".kilo/kilo.jsonc" ]]; then
    target=".kilo/skills/superpowers"
  fi
  log "kilocode adapter target: $target"
  ln_to_skills "$target"
}

dispatch_devin() {
  ensure_submodule
  ln_to_skills ".agents/skills/superpowers"
}

dispatch_antigravity() {
  ensure_submodule
  ln_to_skills ".agents/skills/superpowers"
}

dispatch_unknown() {
  ensure_submodule
  ln_to_skills ".agents/skills/superpowers"
  warn "Unknown platform — defaulted to submodule + .agents/skills/superpowers symlink."
  warn "If your platform supports plugin marketplaces, prefer those instead."
}

# ----------------------------------------------------------------------------
# uninstall
# ----------------------------------------------------------------------------

run_uninstall() {
  log "uninstall: tearing down submodule + symlinks"
  for adapter in .kilocode/skills/superpowers .kilo/skills/superpowers .agents/skills/superpowers; do
    unlink_adapter "$adapter"
  done
  remove_submodule
  log "uninstall complete (re-run install with $0 --apply to restore)"
}

# ----------------------------------------------------------------------------
# --check (used by pre-commit)
# ----------------------------------------------------------------------------

run_check() {
  local rc=0
  if [[ ! -f "$SP_RC" ]]; then
    warn "$SP_RC missing"
    rc=1
  else
    # Required-keys sanity check (does not need PyYAML).
    for key in version upstream upstream_ref fallback_path install_mode active_skills; do
      if ! grep -qE "^${key}:" "$SP_RC"; then
        warn "$SP_RC missing required key: $key"
        rc=1
      fi
    done
    # Optional full YAML parse — only when PyYAML is reachable.
    if python3 -c "import yaml" 2>/dev/null; then
      if ! python3 -c "import yaml; yaml.safe_load(open('$SP_RC'))" 2>/dev/null; then
        warn "$SP_RC is not valid YAML"
        rc=1
      fi
    fi
  fi
  # Submodule presence is best-effort: contributors may not have run
  # `git submodule update --init`. We only flag if .gitmodules references it
  # but the dir is missing entirely.
  if grep -qs "path = $SUBMODULE_PATH$" .gitmodules 2>/dev/null; then
    if [[ ! -d "$SUBMODULE_PATH" ]]; then
      warn "$SUBMODULE_PATH listed in .gitmodules but missing on disk"
      warn "  fix: git submodule update --init --recursive $SUBMODULE_PATH"
      rc=1
    fi
  fi
  if [[ $rc -eq 0 ]]; then log "check: ok"; else log "check: failed"; fi
  exit $rc
}

# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

main() {
  if [[ "$CHECK" -eq 1 ]]; then run_check; fi
  if [[ "$UNINSTALL" -eq 1 ]]; then run_uninstall; require_apply; exit 0; fi

  local platform
  platform=$(detect_platform)
  log "platform=$platform apply=$APPLY upstream=$UPSTREAM_REF"

  case "$platform" in
    claudecode|cursor|codex-cli|codex-app|copilot-cli|gemini)
      dispatch_native "$platform"
      ;;
    opencode)
      dispatch_opencode
      ;;
    kilocode)
      dispatch_kilocode
      ;;
    hermes)
      dispatch_hermes
      ;;
    devin)
      dispatch_devin
      ;;
    antigravity)
      dispatch_antigravity
      ;;
    unknown)
      dispatch_unknown
      ;;
    *)
      die "unsupported --mode=$platform"
      ;;
  esac

  require_apply
  log "done"
}

main "$@"
