"""Admin-observer guardrails for tandem managers.

A small subset of league participants — currently ``whiplash 92`` and
``AleX TiiKii`` — occasionally appear on another team's roster purely
for *observation / admin oversight*. Per the league owner, those
appearances are **not** real tandems and the team's playoff results
must NOT be split between the active manager and the observer.

At the same time, the observers are themselves regular participants
elsewhere — their solo achievements (~10 across L1 and L2) are
legitimate and must keep flowing through the rating engine untouched.

The exception is therefore narrowly scoped to a single creation point:
**a manager record whose name encodes a tandem (``Tandem: A, B``) and
whose pair includes an observer**. By default such a record is rejected;
to register a *real* tandem with an observer (it does happen — the
22/23 L2 ``Tandem: Vlad, whiplash 92`` is a documented case), the pair
must be added to ``data/seed/explicit_tandems.json``.

This module provides:

- ``ADMIN_OBSERVERS`` — the canonical set of observer names.
- ``normalize`` / ``is_admin_observer`` — case-insensitive lookup
  helpers (so ``alex tiikii`` and ``AleX TiiKii`` both trigger).
- ``parse_tandem_members`` — splits ``Tandem: A, B`` into members.
- ``load_explicit_tandems`` — reads the allowlist JSON.
- ``validate_manager_name`` — the actual guardrail used by
  :mod:`data.seed_service` and the Flask-Admin views in
  :mod:`services.admin.views`.

The rule is applied lazily and never raises for non-tandem names, so
solo observer rows (``whiplash 92`` itself, ``AleX TiiKii`` itself)
slide through without inspection.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

# Canonical spellings — the values shown in Flask-Admin and the seed
# JSON. Comparison itself is case-insensitive (see ``normalize``); the
# canonical form is preserved for human-facing error messages.
ADMIN_OBSERVERS: Final[frozenset[str]] = frozenset({"whiplash 92", "AleX TiiKii"})

# Default path for the explicit-tandem allowlist. Resolved at call time
# in ``load_explicit_tandems`` so tests can override it cleanly.
_DEFAULT_ALLOWLIST_PATH: Final[Path] = Path(__file__).parent / "seed" / "explicit_tandems.json"

# Manager-name format used everywhere in the project.
_TANDEM_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^\s*tandem\s*:\s*", re.IGNORECASE)


def normalize(name: str) -> str:
    """Return a lookup-friendly form of a manager name.

    Lowercases, trims, and collapses internal whitespace runs to a
    single space — so ``"  AleX  TiiKii "`` and ``"alex tiikii"`` both
    map to ``"alex tiikii"``.
    """

    return re.sub(r"\s+", " ", name.strip().lower())


_NORMALIZED_OBSERVERS: Final[frozenset[str]] = frozenset(
    normalize(observer) for observer in ADMIN_OBSERVERS
)


def is_admin_observer(name: str) -> bool:
    """Return ``True`` if ``name`` is one of the configured observers."""

    return normalize(name) in _NORMALIZED_OBSERVERS


def parse_tandem_members(name: str) -> list[str] | None:
    """Split ``"Tandem: A, B"`` into ``["A", "B"]`` (originals preserved).

    Returns ``None`` for non-tandem names. The ``Tandem:`` prefix match
    is case- and whitespace-insensitive; the member names themselves
    are stripped of surrounding whitespace but otherwise unchanged.
    Empty / whitespace-only members are dropped.
    """

    match = _TANDEM_PREFIX_RE.match(name)
    if not match:
        return None
    body = name[match.end() :]
    members = [piece.strip() for piece in body.split(",")]
    return [m for m in members if m]


def tandem_observer_members(name: str) -> tuple[str, ...]:
    """Return tandem members that match the observer list (originals).

    Returns an empty tuple for non-tandem names or tandems with no
    observer members. Member names returned are the *originals* from
    ``name`` (not the canonical observer spelling), so callers can
    surface them verbatim in error messages.
    """

    members = parse_tandem_members(name)
    if not members:
        return ()
    return tuple(m for m in members if is_admin_observer(m))


def load_explicit_tandems(path: Path | None = None) -> frozenset[frozenset[str]]:
    """Load the allowlist as a set of frozensets-of-normalized-members.

    The allowlist file is a flat JSON list of canonical tandem-name
    strings, e.g. ``["Tandem: Vlad, whiplash 92"]``. We index by the
    *set* of normalized member names so order doesn't matter — both
    ``"Tandem: Vlad, whiplash 92"`` and the swapped variant resolve to
    the same key.

    Missing / empty files are treated as an empty allowlist (callers
    can always grow it later). Malformed entries (non-tandem strings)
    are silently ignored — keeping the JSON forgiving while the rest
    of the validator handles the actual matching.
    """

    target = path or _DEFAULT_ALLOWLIST_PATH
    if not target.exists():
        return frozenset()
    with target.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    allowlist: set[frozenset[str]] = set()
    for entry in raw:
        members = parse_tandem_members(entry)
        if not members:
            continue
        allowlist.add(frozenset(normalize(m) for m in members))
    return frozenset(allowlist)


def is_explicit_tandem(name: str, allowlist: frozenset[frozenset[str]] | None = None) -> bool:
    """Return ``True`` if ``name`` is registered as an explicit tandem."""

    members = parse_tandem_members(name)
    if not members:
        return False
    key = frozenset(normalize(m) for m in members)
    if allowlist is None:
        allowlist = load_explicit_tandems()
    return key in allowlist


def validate_manager_name(name: str, allowlist: frozenset[frozenset[str]] | None = None) -> None:
    """Raise ``ValueError`` if ``name`` is an admin-observer tandem.

    The guardrail only triggers for tandem-formatted names that pair an
    observer with another participant **and** that are not registered
    in the explicit-tandem allowlist. All other names — including solo
    observer rows — pass through untouched.
    """

    observers_in_pair = tandem_observer_members(name)
    if not observers_in_pair:
        return
    if is_explicit_tandem(name, allowlist):
        return
    observer_list = ", ".join(observers_in_pair)
    raise ValueError(
        f"Manager '{name}' couples another participant with admin observer "
        f"'{observer_list}'. Admin-observer rosters are not tandems by default. "
        f"If this pair really played as a tandem, add the exact name to "
        f"data/seed/explicit_tandems.json to bypass this guardrail."
    )
