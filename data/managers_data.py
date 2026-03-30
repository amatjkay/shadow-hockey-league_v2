"""Initial data for Shadow Hockey League managers.

This module contains the seed data for managers, countries, and achievements.
Each manager has a name, country flag path, and optional list of achievement HTML strings.

Usage:
    from data.managers_data import managers
"""

from dataclasses import dataclass
from typing import List, Optional

# Path constants for static assets
CUPS_PATH = "/static/img/cups/"
FLAGS_PATH = "/static/img/flags/"

# Achievement icon files (all SVG format)
CUP_TOP1 = f"{CUPS_PATH}top1.svg"
CUP_TOP2 = f"{CUPS_PATH}top2.svg"
CUP_TOP3 = f"{CUPS_PATH}top3.svg"
CUP_BEST = f"{CUPS_PATH}best-reg.svg"
CUP_R3 = f"{CUPS_PATH}clap-b.svg"
CUP_R1 = f"{CUPS_PATH}clap.svg"

# Flag files (all PNG format)
FLAG_RUS = f"{FLAGS_PATH}rus.png"
FLAG_BEL = f"{FLAGS_PATH}bel.png"
FLAG_KZ = f"{FLAGS_PATH}kz.png"
FLAG_VIETNAM = f"{FLAGS_PATH}vietnam.png"
FLAG_UA = f"{FLAGS_PATH}ua.png"
FLAG_MEXICO = f"{FLAGS_PATH}mexico.png"
FLAG_POL = f"{FLAGS_PATH}pol.png"
FLAG_CHINA = f"{FLAGS_PATH}china.png"


@dataclass
class ManagerData:
    """Data class representing a manager with their achievements."""

    name: str
    country: str
    achievements: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.achievements is None:
            self.achievements = []


# List of countries (for reference, not directly used in seeding)
COUNTRIES = ["Russia", "Belarus", "Kazakhstan", "Vietnam", "Ukraine", "Mexico", "Poland", "China"]

# Managers data - used by seed_db.py to populate the database
# Note: Max Trufanov appears once with all 3 achievements (consolidated from duplicate entries)
managers = [
    ManagerData(
        "Feel Good",
        FLAG_BEL,
        [
            f'<img src="{CUP_TOP1}" title="Shadow 1 league TOP1 s22/23">',
            f'<img src="{CUP_TOP2}" title="Shadow 1 league TOP2 s21/22">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s23/24">',
        ],
    ),
    ManagerData(
        "Sousse Sousse", FLAG_RUS, [f'<img src="{CUP_TOP1}" title="Shadow 1 league TOP1 s23/24">']
    ),
    ManagerData(
        "Cole CaufieldTeamNePobedim",
        FLAG_KZ,
        [f'<img src="{CUP_TOP1}" title="Shadow 1 league TOP1 s21/22">'],
    ),
    ManagerData(
        "whiplash 92",
        FLAG_RUS,
        [
            f'<img src="{CUP_TOP2}" title="Shadow 1 league TOP2 s23/24">',
            f'<img src="{CUP_TOP3}" title="Shadow 1 league TOP3 s21/22">',
            f'<img src="{CUP_BEST}" title="Shadow 1 league Best regular player s23/24">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s22/23">',
        ],
    ),
    ManagerData(
        "Alex Galuza",
        FLAG_BEL,
        [
            f'<img src="{CUP_TOP2}" title="Shadow 1 league TOP2 s22/23">',
            f'<img src="{CUP_BEST}" title="Shadow 1 league Best regular player s22/23">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s21/22">',
        ],
    ),
    ManagerData(
        "El Guerrero", FLAG_BEL, [f'<img src="{CUP_TOP3}" title="Shadow 1 league TOP3 s23/24">']
    ),
    ManagerData(
        "Max Bumble", FLAG_RUS, [f'<img src="{CUP_TOP1}" title="Shadow 2 league TOP1 s23/24">']
    ),
    ManagerData(
        "Sumzair San", FLAG_RUS, [f'<img src="{CUP_TOP1}" title="Shadow 2 league TOP1 s22/23">']
    ),
    ManagerData(
        "AleX TiiKii",
        FLAG_RUS,
        [
            f'<img src="{CUP_TOP2}" title="Shadow 2 league TOP2 s22/23">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s23/24">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s21/22">',
        ],
    ),
    ManagerData(
        "Сергей Стрельченко",
        FLAG_BEL,
        [f'<img src="{CUP_TOP2}" title="Shadow 2 league TOP2 s23/24">'],
    ),
    ManagerData(
        "Yoze Marino", FLAG_CHINA, [f'<img src="{CUP_TOP3}" title="Shadow 2 league TOP3 s23/24">']
    ),
    ManagerData(
        "Nurzhan Yessengaliev",
        FLAG_KZ,
        [
            f'<img src="{CUP_TOP3}" title="Shadow 1 league TOP3 s22/23">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s23/24">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s21/22">',
        ],
    ),
    ManagerData(
        "Tandem: Vlad, whiplash 92",
        FLAG_RUS,
        [f'<img src="{CUP_TOP3}" title="Shadow 2 league TOP3 s22/23">'],
    ),
    ManagerData(
        "Евгений Иванов",
        FLAG_RUS,
        [
            f'<img src="{CUP_BEST}" title="Shadow 1 league Best regular player s21/22">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s22/23">',
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s21/22">',
        ],
    ),
    ManagerData(
        "Vladislav Belov",
        FLAG_VIETNAM,
        [
            f'<img src="{CUP_BEST}" title="Shadow 2 league Best regular player s21/22">',
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s21/22">',
        ],
    ),
    ManagerData(
        "Евгений Медведев",
        FLAG_RUS,
        [f'<img src="{CUP_R3}" title="Shadow 1 league Round 3 s23/24">'],
    ),
    ManagerData(
        "Aleks Lang", FLAG_RUS, [f'<img src="{CUP_R3}" title="Shadow 2 league Round 3 s23/24">']
    ),
    ManagerData(
        "Vyacheslav Shamanov",
        FLAG_RUS,
        [f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s23/24">'],
    ),
    ManagerData(
        "Sergey Kharlanov",
        FLAG_BEL,
        [f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s22/23">'],
    ),
    ManagerData(
        "Denis Sanzharevskyi",
        FLAG_UA,
        [f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s21/22">'],
    ),
    ManagerData(
        "Don Georgio",
        FLAG_RUS,
        [
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s23/24">',
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s24/25">',
        ],
    ),
    ManagerData(
        "Юрий Shestakov",
        FLAG_RUS,
        [
            f'<img src="{CUP_BEST}" title="Shadow 2 league Best regular s24/25">',
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s23/24">',
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s24/25">',
        ],
    ),
    ManagerData(
        "Vlad V", FLAG_RUS, [f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s23/24">']
    ),
    ManagerData(
        "Tandem: Sergey Dorokhov, Maxim Shvetsov",
        FLAG_RUS,
        [f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s23/24">'],
    ),
    ManagerData("Павел Роевнев", FLAG_RUS),
    ManagerData("Igor Kadzayev", FLAG_MEXICO),
    ManagerData("Oleg Karandashov", FLAG_UA),
    ManagerData("Andrii Korniichuk", FLAG_POL),
    ManagerData(
        "Dima ATC", FLAG_RUS, [f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s24/25">']
    ),
    ManagerData(
        "Alex Rybakov", FLAG_RUS, [f'<img src="{CUP_TOP1}" title="Shadow 2 league TOP1 s24/25">']
    ),
    ManagerData("Femida Femida", FLAG_RUS),
    ManagerData("Maxim Shvetsov", FLAG_RUS),
    ManagerData("Sergey Dorokhov", FLAG_RUS),
    ManagerData(
        "Zhanabil Au", FLAG_KZ, [f'<img src="{CUP_R3}" title="Shadow 2 league Round 3 s24/25">']
    ),
    ManagerData(
        "xMoneyMaker 1", FLAG_RUS, [f'<img src="{CUP_TOP2}" title="Shadow 2 league TOP2 s24/25">']
    ),
    ManagerData(
        "Aleksejs Lazarenko",
        FLAG_RUS,
        [f'<img src="{CUP_TOP3}" title="Shadow 2 league TOP3 s24/25">'],
    ),
    ManagerData("Dias Kazbekuly", FLAG_RUS),
    ManagerData("Tandem: Vladislav B, Ilnaz Akhtyamov", FLAG_RUS),
    ManagerData("Sergey Pashkov", FLAG_RUS),
    ManagerData("Ruslan Shlain", FLAG_RUS),
    ManagerData("Dmitrii Volkov", FLAG_RUS),
    ManagerData(
        "Max Trufanov",
        FLAG_UA,
        [
            f'<img src="{CUP_R1}" title="Shadow 1 league Round 1 s22/23">',
            f'<img src="{CUP_R3}" title="Shadow 1 league Round 3 s21/22">',
            f'<img src="{CUP_R1}" title="Shadow 2 league Round 1 s24/25">',
        ],
    ),
]
