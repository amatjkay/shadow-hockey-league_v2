"""Centralized static asset path resolution.

This module is the single source of truth for all static asset paths
(flags, cups, etc.). It eliminates hardcoded paths scattered across
the codebase.

Usage:
    from data.static_paths import StaticPaths

    paths = StaticPaths()
    flag_url = paths.resolve_flag("RUS.png")  # /static/img/flags/RUS.png
    cup_url = paths.resolve_cup("top1.svg")   # /static/img/cups/top1.svg
    country_code = paths.flag_to_code("BLR")  # BLR
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class StaticPaths:
    """Centralized static asset path resolution.

    Attributes:
        BASE: Base URL path for all static images.
        FLAGS_DIR: Local filesystem path to flags directory.
        CUPS_DIR: Local filesystem path to cups directory.
    """

    # Base URL path for all static images
    BASE = "/static/img"

    # Subdirectories
    FLAGS_SUBDIR = "flags"
    CUPS_SUBDIR = "cups"

    # URL paths
    FLAGS_URL = f"{BASE}/{FLAGS_SUBDIR}"
    CUPS_URL = f"{BASE}/{CUPS_SUBDIR}"

    # Filesystem paths (resolved relative to project root)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    FLAGS_DIR = PROJECT_ROOT / "static" / "img" / "flags"
    CUPS_DIR = PROJECT_ROOT / "static" / "img" / "cups"

    # Flag filename to country code mapping.
    # This replaces the hardcoded FLAG_TO_CODE dict that was in seed_db.py.
    # Key: filename (without extension), Value: ISO 3166-1 alpha-3 code.
    FLAG_TO_CODE: dict[str, str] = {
        "RUS": "RUS",
        "BLR": "BLR",
        "BEL": "BLR",  # Legacy: old Belgium flag is actually Belarus
        "KAZ": "KAZ",
        "KZ": "KAZ",  # Legacy: old filename
        "VNM": "VNM",
        "VIETNAM": "VNM",  # Legacy: old filename
        "UKR": "UKR",
        "UA": "UKR",  # Legacy: old filename
        "MEX": "MEX",
        "MEXICO": "MEX",  # Legacy: old filename
        "POL": "POL",
        "CHN": "CHN",
        "CHINA": "CHN",  # Legacy: old filename
        "CAN": "CAN",
        "FIN": "FIN",
        "SWE": "SWE",
        "CZE": "CZE",
        "SVK": "SVK",
        "GER": "GER",
        "SUI": "SUI",
        "AUT": "AUT",
        "NOR": "NOR",
        "DEN": "DEN",
        "FRA": "FRA",
        "GBR": "GBR",
        "LAT": "LAT",
        "USA": "USA",
    }

    # Legacy flag filename to canonical filename mapping.
    # Handles the migration from old lowercase names to ISO codes.
    LEGACY_FLAG_MAP: dict[str, str] = {
        "bel.png": "BLR.png",
        "rus.png": "RUS.png",
        "kz.png": "KAZ.png",
        "china.png": "CHN.png",
        "mexico.png": "MEX.png",
        "ua.png": "UKR.png",
        "vietnam.png": "VNM.png",
        "pol.png": "POL.png",
        # Lowercase to uppercase normalization
        "blr.png": "BLR.png",
        "kaz.png": "KAZ.png",
        "ukr.png": "UKR.png",
        "chn.png": "CHN.png",
        "mex.png": "MEX.png",
        "vnm.png": "VNM.png",
    }

    # Reverse mapping: country code → canonical flag filename
    CODE_TO_FLAG: dict[str, str] = {}

    def __init__(self) -> None:
        """Initialize reverse mapping on creation."""
        self._build_code_to_flag_mapping()

    def _build_code_to_flag_mapping(self) -> None:
        """Build reverse mapping from country code to canonical flag filename.

        For codes with multiple flag files (e.g. legacy), uses the canonical one.
        """
        seen_codes: set[str] = set()
        # Iterate in reverse so canonical entries overwrite legacy ones
        for filename, code in reversed(list(self.FLAG_TO_CODE.items())):
            if code not in seen_codes:
                self.CODE_TO_FLAG[code] = filename
                seen_codes.add(code)

    def resolve_flag(self, filename: str) -> str:
        """Resolve a flag filename to its full URL path.

        Handles legacy filenames (e.g. bel.png → BLR.png) automatically.

        Args:
            filename: Flag filename (e.g. "RUS.png", "BLR", or legacy "bel.png").

        Returns:
            Full URL path (e.g. "/static/img/flags/BLR.png").
        """
        # Normalize to canonical filename
        base = filename.lower()
        if base in self.LEGACY_FLAG_MAP:
            filename = self.LEGACY_FLAG_MAP[base]
        elif not filename.endswith(".png"):
            filename = f"{filename}.png"
        return f"{self.FLAGS_URL}/{filename}"

    def resolve_cup(self, filename: str) -> str:
        """Resolve a cup filename to its full URL path.

        Args:
            filename: Cup filename (e.g. "top1.svg").

        Returns:
            Full URL path (e.g. "/static/img/cups/top1.svg").
        """
        return f"{self.CUPS_URL}/{filename}"

    def flag_to_code(self, filename: str) -> Optional[str]:
        """Convert a flag filename to country code.

        Args:
            filename: Flag filename (e.g. "BLR.png" or "BLR").

        Returns:
            ISO 3166-1 alpha-3 country code, or None if not found.
        """
        # Strip extension if present
        base = filename.replace(".png", "").upper()
        return self.FLAG_TO_CODE.get(base)

    def code_to_flag(self, code: str) -> Optional[str]:
        """Convert a country code to flag filename.

        Args:
            code: ISO 3166-1 alpha-3 country code (e.g. "RUS").

        Returns:
            Flag filename (e.g. "RUS.png"), or None if not found.
        """
        filename = self.CODE_TO_FLAG.get(code.upper())
        if filename:
            return f"{filename}.png"
        return None

    def get_available_flags(self) -> list[str]:
        """List all available flag files on disk.

        Returns:
            Sorted list of flag filenames (e.g. ["BLR.png", "RUS.png", ...]).
        """
        if not self.FLAGS_DIR.exists():
            return []
        return sorted(f.name for f in self.FLAGS_DIR.glob("*.png"))

    def get_available_cups(self) -> list[str]:
        """List all available cup files on disk.

        Returns:
            Sorted list of cup filenames (e.g. ["best-reg.svg", "top1.svg", ...]).
        """
        if not self.CUPS_DIR.exists():
            return []
        return sorted(f.name for f in self.CUPS_DIR.glob("*.svg"))

    def get_flag_choices(self) -> list[tuple[str, str]]:
        """Get flag choices for admin form dropdown.

        Returns:
            List of (value, label) tuples for WTForms SelectField.
        """
        flags = self.get_available_flags()
        return [(self.resolve_flag(f), f.replace(".png", "")) for f in flags]


# Module-level singleton for convenient imports
_paths = StaticPaths()

# Convenience aliases (backward compatibility for code that used old constants)
FLAGS_PATH = StaticPaths.FLAGS_URL + "/"
CUPS_PATH = StaticPaths.CUPS_URL + "/"


def resolve_flag(filename: str) -> str:
    """Convenience function to resolve a flag filename.

    Handles legacy filenames (bel.png, rus.png, etc.) automatically.
    """
    return _paths.resolve_flag(filename)


def resolve_cup(filename: str) -> str:
    """Convenience function to resolve a cup filename."""
    return _paths.resolve_cup(filename)


def get_flag_choices() -> list[tuple[str, str]]:
    """Convenience function for admin form choices."""
    return _paths.get_flag_choices()
