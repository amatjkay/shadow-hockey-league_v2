"""Export service for dumping database data to JSON files.

Reads data from the database and writes to data/export/*.json files.
Used for backup and synchronization with seed files.

Usage:
    from data.export_service import ExportService

    service = ExportService(db.session)
    result = service.export_all()
    print(result)  # {'countries': 8, 'managers': 42, 'achievements': 49}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from models import Achievement, Country, Manager

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting database data to JSON files.

    Args:
        session: SQLAlchemy database session.
        export_dir: Path to directory for export files.
    """

    def __init__(self, session: Any, export_dir: str | Path | None = None) -> None:
        self.session = session
        self.export_dir = Path(export_dir) if export_dir else Path(__file__).parent / "export"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> dict[str, int]:
        """Export all data to JSON files.

        Returns:
            Dictionary with counts of exported records.
        """
        countries = self.export_countries()
        managers = self.export_managers()
        achievements = self.export_achievements()

        return {
            "countries": countries,
            "managers": managers,
            "achievements": achievements,
        }

    def export_countries(self) -> int:
        """Export countries to JSON.

        Returns:
            Number of exported records.
        """
        countries = []
        for c in self.session.query(Country).all():
            countries.append({
                "code": c.code,
                "name": c.name,
                "flag_filename": c.flag_path.split("/")[-1],
            })

        filepath = self.export_dir / "countries.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(countries, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(countries)} countries to {filepath}")
        return len(countries)

    def export_managers(self) -> int:
        """Export managers to JSON.

        Returns:
            Number of exported records.
        """
        managers = []
        for m in self.session.query(Manager).all():
            country = self.session.get(Country, m.country_id)
            managers.append({
                "name": m.name,
                "country_code": country.code if country else "???",
            })

        filepath = self.export_dir / "managers.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(managers, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(managers)} managers to {filepath}")
        return len(managers)

    def export_achievements(self) -> int:
        """Export achievements to JSON.

        Returns:
            Number of exported records.
        """
        achievements = []
        for a in self.session.query(Achievement).all():
            manager = self.session.get(Manager, a.manager_id)
            achievements.append({
                "manager_name": manager.name if manager else "???",
                "type": a.achievement_type,
                "league": a.league,
                "season": a.season,
                "title": a.title,
                "icon_filename": a.icon_path.split("/")[-1],
            })

        filepath = self.export_dir / "achievements.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(achievements, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(achievements)} achievements to {filepath}")
        return len(achievements)
