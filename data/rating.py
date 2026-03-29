"""Расчёт рейтинга: база по типу награды и лиге × множитель сезона."""

from __future__ import annotations

import re
from typing import Any

from data.managers_data import managers

BASE_POINTS: dict[tuple[str, str], int] = {
    ("1", "TOP1"): 600,
    ("1", "TOP2"): 500,
    ("1", "TOP3"): 400,
    ("2", "TOP1"): 300,
    ("2", "TOP2"): 200,
    ("2", "TOP3"): 100,
    ("1", "BEST"): 50,
    ("2", "BEST"): 40,
    ("1", "R3"): 30,
    ("2", "R3"): 20,
    ("1", "R1"): 10,
    ("2", "R1"): 5,
}

SEASON_MULTIPLIER: dict[str, float] = {
    "24/25": 1.00,
    "23/24": 1.15,
    "22/23": 1.00,
    "21/22": 0.85,
}

LABEL_RU = {
    "TOP1": "TOP1",
    "TOP2": "TOP2",
    "TOP3": "TOP3",
    "BEST": "Best regular",
    "R3": "Round 3",
    "R1": "Round 1",
}


def _parse_kind(title: str) -> str:
    if title.startswith("TOP"):
        return title
    if "Best regular" in title:
        return "BEST"
    if "Round 3" in title:
        return "R3"
    if "Round 1" in title:
        return "R1"
    return title


def parse_achievement_html(html: str) -> dict[str, Any] | None:
    if "toxic" in html.lower():
        return {
            "points": 0,
            "base": 0,
            "mul": 1.0,
            "mul_display": "1,00",
            "season": None,
            "league": None,
            "kind": "toxic",
            "label": "toxic",
            "html": html,
        }
    m = re.search(r"Shadow (\d+) league (.+?) s([^\"]+)", html)
    if not m:
        return None
    league, title, season = m.group(1), m.group(2).strip(), m.group(3)
    kind = _parse_kind(title)
    base = BASE_POINTS.get((league, kind), 0)
    mul = SEASON_MULTIPLIER.get(season, 1.0)
    points = round(base * mul)
    lab = LABEL_RU.get(kind, kind)
    mul_display = f"{mul:.2f}".replace(".", ",")
    return {
        "points": points,
        "base": base,
        "mul": mul,
        "mul_display": mul_display,
        "season": season,
        "league": league,
        "kind": kind,
        "label": f"Л{league} · {lab} · s{season}",
        "html": html,
    }


def build_leaderboard() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mgr in managers:
        achievements: list[dict[str, Any]] = []
        total = 0
        for raw in mgr.achievements:
            parsed = parse_achievement_html(raw)
            if parsed is None:
                continue
            achievements.append(parsed)
            total += parsed["points"]
        rows.append(
            {
                "name": mgr.name,
                "country": mgr.country,
                "total": total,
                "achievements": achievements,
                "is_tandem": mgr.name.startswith("Tandem:"),
            }
        )
    rows.sort(key=lambda r: (-r["total"], r["name"]))
    out: list[dict[str, Any]] = []
    rank = 0
    prev_total: int | None = None
    for i, r in enumerate(rows, start=1):
        if r["total"] != prev_total:
            rank = i
            prev_total = r["total"]
        item = dict(r)
        item["rank"] = rank
        out.append(item)
    return out
