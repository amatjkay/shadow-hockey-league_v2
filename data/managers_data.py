from flask import url_for

class Manager:
    def __init__(self, name, country, achievements=None):
        self.name = name
        self.country = country
        self.achievements = achievements or []

# Add the definition of countries
countries = [
    "Russia",
    "Belarus",
    "Kazakhstan",
    "Vietnam",
    "Ukraine",
    "Mexico",
    "Poland",
    "China"
]

managers = [
    Manager("Feel Good", "/static/img/flags/bel.png", [
        '<img src="/static/img/cups/top1.svg" title="Shadow 1 league TOP1 s22/23">',
        '<img src="/static/img/cups/top2.svg" title="Shadow 1 league TOP2 s21/22">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s23/24">'
    ]),
    Manager("Sousse Sousse", "/static/img/flags/rus.png", 
           ['<img src="/static/img/cups/top1.svg" title="Shadow 1 league TOP1 s23/24">']),        
    Manager("Cole CaufieldTeamNePobedim", "/static/img/flags/kz.png",
           ['<img src="/static/img/cups/top1.svg" title="Shadow 1 league TOP1 s21/22">']),   
    Manager("whiplash 92", "/static/img/flags/rus.png", [
        '<img src="/static/img/cups/top2.svg" title="Shadow 1 league TOP2 s23/24">',
        '<img src="/static/img/cups/top3.svg" title="Shadow 1 league TOP3 s21/22">',
        '<img src="/static/img/cups/best-reg.svg" title="Shadow 1 league Best regular player s23/24">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s22/23">'
    ]),   
    Manager("Alex Galuza", "/static/img/flags/bel.png", [
        '<img src="/static/img/cups/top2.svg" title="Shadow 1 league TOP2 s22/23">',
        '<img src="/static/img/cups/best-reg.svg" title="Shadow 1 league Best regular player s22/23">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s21/22">'
    ]),
    Manager("El Guerrero", "/static/img/flags/bel.png",
           ['<img src="/static/img/cups/top3.svg" title="Shadow 1 league TOP3 s23/24">']),
    Manager("Max Bumble", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/top1.svg" title="Shadow 2 league TOP1 s23/24">']),

    Manager("Sumzair San", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/top1.svg" title="Shadow 2 league TOP1 s22/23">']),
    Manager("AleX TiiKii", "/static/img/flags/rus.png", [
        '<img src="/static/img/cups/top2.svg" title="Shadow 2 league TOP2 s22/23">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s23/24">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s21/22">'
    ]),
    Manager("Сергей Стрельченко", "/static/img/flags/bel.png",
           ['<img src="/static/img/cups/top2.svg" title="Shadow 2 league TOP2 s23/24">']),
    Manager("Yoze Marino", "/static/img/flags/china.png",
           ['<img src="/static/img/cups/top3.svg" title="Shadow 2 league TOP3 s23/24">']),
    
    Manager("Nurzhan Yessengaliev", "/static/img/flags/kz.png", [
        '<img src="/static/img/cups/top3.svg" title="Shadow 1 league TOP3 s22/23">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s23/24">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s21/22">'
    ]),
    Manager("Tandem: Vlad, whiplash 92", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/top3.svg" title="Shadow 2 league TOP3 s22/23">']),
    Manager("Евгений Иванов", "/static/img/flags/rus.png", [
        '<img src="/static/img/cups/best-reg.svg" title="Shadow 1 league Best regular player s21/22">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s22/23">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s21/22">'
    ]),
    Manager("Vladislav Belov", "/static/img/flags/vietnam.png", [
        '<img src="/static/img/cups/best-reg.svg" title="Shadow 2 league Best regular player s21/22">',
        '<img src="/static/img/cups/clap.svg" title="Shadow 2 league Round 1 s21/22">',
        '<img src="/static/img/cups/toxic.png" title="toxic and unpleasant person">'
    ]),
    Manager("Max Trufanov", "/static/img/flags/ua.png", [
        '<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s22/23">',
        '<img src="/static/img/cups/clap-b.svg" title="Shadow 1 league Round 3 s21/22">'
    ]),
    Manager("Евгений Медведев", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap-b.svg" title="Shadow 1 league Round 3 s23/24">']),
    Manager("Aleks Lang", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap-b.svg" title="Shadow 2 league Round 3 s23/24">']),
    Manager("Vyacheslav Shamanov", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s23/24">']),
    Manager("Sergey Kharlanov", "/static/img/flags/bel.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s22/23">']),
    Manager("Denis Sanzharevskyi", "/static/img/flags/ua.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 1 league Round 1 s21/22">']),
    Manager("Don Georgio", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 2 league Round 1 s23/24">']),
    Manager("Юрий Shestakov", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 2 league Round 1 s23/24">']),
    Manager("Vlad V", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 2 league Round 1 s23/24">']),
    Manager("Tandem: Sergey Dorokhov, Maxim Shvetsov", "/static/img/flags/rus.png",
           ['<img src="/static/img/cups/clap.svg" title="Shadow 2 league Round 1 s23/24">']),
    Manager("Павел Роевнев", "/static/img/flags/rus.png"),
    Manager("Igor Kadzayev", "/static/img/flags/mexico.png"),
    Manager("Oleg Karandashov", "/static/img/flags/ua.png"),
    Manager("Andrii Korniichuk", "/static/img/flags/pol.png"),
    Manager("Dima ATC", "/static/img/flags/rus.png"),
    Manager("Alex Rybakov", "/static/img/flags/rus.png"),
    Manager("Femida Femida", "/static/img/flags/rus.png"),
    Manager("Maxim Shvetsov", "/static/img/flags/rus.png"),
    Manager("Sergey Dorokhov", "/static/img/flags/rus.png"),
    Manager("Zhanabil Au", "/static/img/flags/kz.png"),
    Manager("xMoneyMaker 1", "/static/img/flags/rus.png")
]