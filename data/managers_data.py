from flask import url_for

leagues = ["1", "2"]

countries = [
    "static/img/flags/rus.png",
    "static/img/flags/bel.png",
    "static/img/flags/kz.png",
    "static/img/flags/vietnam.png",
    "static/img/flags/ua.png",
    "static/img/flags/mexico.png",
    "static/img/flags/pol.png",
    "static/img/flags/china.png",
    "static/img/flags/shit.png",
]

def create_achievement(league, cup, season, title):
    return f'<img src="/static/img/cups/{cup}.svg" title="Shadow {league} league {title} {season}">'

achievements = {
    "Primary_league": {
        "top1_2122": create_achievement(leagues[0], "top1", "s21/22", "TOP1"),
        "top1_2223": create_achievement(leagues[0], "top1", "s22/23", "TOP1"),
        "top1_2324": create_achievement(leagues[0], "top1", "s23/24", "TOP1"),
        "top2_2122": create_achievement(leagues[0], "top2", "s21/22", "TOP2"),
        "top2_2223": create_achievement(leagues[0], "top2", "s22/23", "TOP2"),
        "top2_2324": create_achievement(leagues[0], "top2", "s23/24", "TOP2"),
        "top3_2122": create_achievement(leagues[0], "top3", "s21/22", "TOP3"),
        "top3_2223": create_achievement(leagues[0], "top3", "s22/23", "TOP3"),
        "top3_2324": create_achievement(leagues[0], "top3", "s23/24", "TOP3"),
        "bestRegPlayer_2122": create_achievement(leagues[0], "best-reg", "s21/22", "Best regular player"),
        "bestRegPlayer_2223": create_achievement(leagues[0], "best-reg", "s22/23", "Best regular player"),
        "bestRegPlayer_2224": create_achievement(leagues[0], "best-reg", "s23/24", "Best regular player"),
        "round1_2122": create_achievement(leagues[0], "clap", "s21/22", "Round 1"),
        "round1_2223": create_achievement(leagues[0], "clap", "s22/23", "Round 1"),
        "round1_2324": create_achievement(leagues[0], "clap", "s23/24", "Round 1"),
        "round2_2122": create_achievement(leagues[0], "clap", "s21/22", "Round 2"),
        "round2_2223": create_achievement(leagues[0], "clap", "s22/23", "Round 2"),
        "round2_2324": create_achievement(leagues[0], "clap", "s23/24", "Round 2"),
        "round3_2122": create_achievement(leagues[0], "clap-b", "s21/22", "Round 3"),
        "round3_2223": create_achievement(leagues[0], "clap-b", "s22/23", "Round 3"),
        "round3_2324": create_achievement(leagues[0], "clap-b", "s23/24", "Round 3"),
        "toxic": '<img src="/static/img/cups/toxic.png" title="toxic and unpleasant person">',
    },
    "Second_league": {
        "top1_2122": create_achievement(leagues[1], "top1", "s21/22", "TOP1"),
        "top1_2223": create_achievement(leagues[1], "top1", "s22/23", "TOP1"),
        "top1_2324": create_achievement(leagues[1], "top1", "s23/24", "TOP1"),
        "top2_2122": create_achievement(leagues[1], "top2", "s21/22", "TOP2"),
        "top2_2223": create_achievement(leagues[1], "top2", "s22/23", "TOP2"),
        "top2_2324": create_achievement(leagues[1], "top2", "s23/24", "TOP2"),
        "top3_2122": create_achievement(leagues[1], "top3", "s21/22", "TOP3"),
        "top3_2223": create_achievement(leagues[1], "top3", "s22/23", "TOP3"),
        "top3_2324": create_achievement(leagues[1], "top3", "s23/24", "TOP3"),
        "bestRegPlayer_2122": create_achievement(leagues[1], "best-reg", "s21/22", "Best regular player"),
        "bestRegPlayer_2223": create_achievement(leagues[1], "best-reg", "s22/23", "Best regular player"),
        "bestRegPlayer_2224": create_achievement(leagues[1], "best-reg", "s23/24", "Best regular player"),
        "round1_2122": create_achievement(leagues[1], "clap", "s21/22", "Round 1"),
        "round1_2223": create_achievement(leagues[1], "clap", "s22/23", "Round 1"),
        "round1_2324": create_achievement(leagues[1], "clap", "s23/24", "Round 1"),
        "round2_2122": create_achievement(leagues[1], "clap", "s21/22", "Round 2"),
        "round2_2223": create_achievement(leagues[1], "clap", "s22/23", "Round 2"),
        "round2_2324": create_achievement(leagues[1], "clap", "s23/24", "Round 2"),
        "round3_2122": create_achievement(leagues[1], "clap-b", "s21/22", "Round 3"),
        "round3_2223": create_achievement(leagues[1], "clap-b", "s22/23", "Round 3"),
        "round3_2324": create_achievement(leagues[1], "clap-b", "s23/24", "Round 3"),
    }
}

managers = [
    {"name": "Sousse Sousse", "country": countries[0], "achievement": [achievements["Primary_league"]["top1_2324"], achievements["Primary_league"]["round3_2223"]]},
    {"name": "whiplash 92", "country": countries[0], "achievement": [
        achievements["Primary_league"]["top2_2324"],
        achievements["Primary_league"]["bestRegPlayer_2224"],
        achievements["Primary_league"]["round1_2223"],
        achievements["Primary_league"]["top3_2122"]
    ]},
    {"name": "El Guerrero", "country": countries[1], "achievement": [achievements["Primary_league"]["top3_2324"]]},
    {"name": "Max Bumble", "country": countries[0], "achievement": [achievements["Second_league"]["top1_2324"]]},
    {"name": "Сергей Стрельченко", "country": countries[1], "achievement": [achievements["Second_league"]["top2_2324"]]},
    {"name": "Yoze Marino", "country": countries[7], "achievement": [achievements["Second_league"]["top3_2324"]]},
    {"name": "Feel Good", "country": countries[1], "achievement": [
        achievements["Primary_league"]["round1_2324"],
        achievements["Primary_league"]["top1_2223"],
        achievements["Primary_league"]["top2_2122"]
    ]},
    {"name": "Cole CaufieldTeamNePobedim", "country": countries[2], "achievement": [achievements["Primary_league"]["top1_2122"]]},
    {"name": "Sumzair San", "country": countries[0], "achievement": [achievements["Second_league"]["top1_2223"]]},
    {"name": "Alex Galuza", "country": countries[1], "achievement": [
        achievements["Primary_league"]["top2_2223"],
        achievements["Primary_league"]["bestRegPlayer_2223"],
        achievements["Primary_league"]["round1_2122"]
    ]},
    {"name": "AleX TiiKii", "country": countries[0], "achievement": [
        achievements["Primary_league"]["round1_2324"],
        achievements["Second_league"]["top2_2223"],
        achievements["Primary_league"]["round1_2122"]
    ]},
    {"name": "Nurzhan Yessengaliev", "country": countries[2], "achievement": [
        achievements["Primary_league"]["round1_2324"],
        achievements["Primary_league"]["top3_2223"],
        achievements["Primary_league"]["round1_2122"]
    ]},
    {"name": "Tandem: Vlad, whiplash 92", "country": countries[0], "achievement": [achievements["Second_league"]["top3_2223"]]},
    {"name": "Евгений Иванов", "country": countries[0], "achievement": [
        achievements["Primary_league"]["round1_2223"],
        achievements["Primary_league"]["bestRegPlayer_2122"],
        achievements["Primary_league"]["round1_2122"]
    ]},
    {"name": "Vladislav Belov", "country": countries[8], "achievement": [
        achievements["Primary_league"]["toxic"],
        achievements["Second_league"]["bestRegPlayer_2122"],
        achievements["Second_league"]["round1_2122"]
    ]},
    {"name": "Max Trufanov", "country": countries[4], "achievement": [achievements["Primary_league"]["round1_2223"], achievements["Primary_league"]["round3_2122"]]},
    {"name": "Евгений Медведев", "country": countries[0], "achievement": [achievements["Primary_league"]["round3_2324"]]},
    {"name": "Aleks Lang", "country": countries[0], "achievement": [achievements["Second_league"]["round3_2324"]]},
    {"name": "Vyacheslav Shamanov", "country": countries[0], "achievement": [achievements["Primary_league"]["round1_2324"]]},
    {"name": "Sergey Kharlanov", "country": countries[1], "achievement": [achievements["Primary_league"]["round1_2223"]]},
    {"name": "Denis Sanzharevskyi", "country": countries[4], "achievement": [achievements["Primary_league"]["round1_2122"]]},
    {"name": "Don Georgio", "country": countries[0], "achievement": [achievements["Second_league"]["round1_2324"]]},
    {"name": "Юрий Shestakov", "country": countries[0], "achievement": [achievements["Second_league"]["round1_2324"]]},
    {"name": "Vlad V", "country": countries[0], "achievement": [achievements["Second_league"]["round1_2324"]]},
    {"name": "Tandem: Sergey Dorokhov, Maxim Shvetsov", "country": countries[0], "achievement": [achievements["Second_league"]["round1_2324"]]},
    {"name": "Павел Роевнев", "country": countries[0], "achievement": []},
    {"name": "Igor Kadzayev", "country": countries[5], "achievement": []},
    {"name": "Oleg Karandashov", "country": countries[4], "achievement": []},
    {"name": "Andrii Korniichuk", "country": countries[6], "achievement": []},
    {"name": "Dima ATC", "country": countries[0], "achievement": []},
    {"name": "Alex Rybakov", "country": countries[0], "achievement": []},
    {"name": "Femida Femida", "country": countries[0], "achievement": []},
    {"name": "Maxim Shvetsov", "country": countries[0], "achievement": []},
    {"name": "Sergey Dorokhov", "country": countries[0], "achievement": []},
    {"name": "Zhanabil Au", "country": countries[2], "achievement": []},
    {"name": "xMoneyMaker 1", "country": countries[0], "achievement": []},
]
