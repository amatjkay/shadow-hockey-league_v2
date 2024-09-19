const leagues = ["1", "2"];

const countries = [
    "../img/flags/rus.png",
    "../img/flags/bel.png",
    "../img/flags/kz.png",
    "../img/flags/vietnam.png",
    "../img/flags/ua.png",
    "../img/flags/mexico.png",
    "../img/flags/pol.png",
    "../img/flags/china.png",
    "../img/flags/shit.png",
];

const achievements = [
    (Primary_league = {
        top1_2122: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[0]} league TOP1 s21/22"></img>`,
        top1_2223: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[0]} league TOP1 s22/23"></img>`,
        top1_2324: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[0]} league TOP1 s23/24"></img>`,
        top2_2122: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[0]} league TOP2 s21/22"></img>`,
        top2_2223: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[0]} league TOP2 s22/23"></img>`,
        top2_2324: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[0]} league TOP2 s23/24"></img>`,
        top3_2122: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[0]} league TOP3 s21/22"></img>`,
        top3_2223: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[0]} league TOP3 s22/23"></img>`,
        top3_2324: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[0]} league TOP3 s23/24"></img>`,
        bestRegPlayer_2122: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[0]} league Best regular player s21/22"></img>`,
        bestRegPlayer_2223: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[0]} league Best regular player s22/23"></img>`,
        bestRegPlayer_2224: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[0]} league Best regular player s23/24"></img>`,
        round1_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 1 s21/22"></img>`,
        round1_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 1 s22/23"></img>`,
        round1_2324: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 1 s23/24"></img>`,
        round2_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 2 s21/22"></img>`,
        round2_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 2 s22/23"></img>`,
        round2_2324: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 2 s23/24"></img>`,
        round3_2122: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[0]} league Round 3 s21/22"></img>`,
        round3_2223: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[0]} league Round 3 s22/23"></img>`,
        round3_2324: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[0]} league Round 3 s23/24"></img>`,
        toxic: `<img src="../img/cups/toxic.png" title="toxic and unpleasant person"></img>`,
    }),
    (Second_league = {
        top1_2122: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[1]} league TOP1 s21/22"></img>`,
        top1_2223: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[1]} league TOP1 s22/23"></img>`,
        top1_2324: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[1]} league TOP1 s23/24"></img>`,
        top2_2122: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[1]} league TOP2 s21/22"></img>`,
        top2_2223: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[1]} league TOP2 s22/23"></img>`,
        top2_2324: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[1]} league TOP2 s23/24"></img>`,
        top3_2122: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[1]} league TOP3 s21/22"></img>`,
        top3_2223: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[1]} league TOP3 s22/23"></img>`,
        top3_2324: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[1]} league TOP3 s23/24"></img>`,
        bestRegPlayer_2122: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[1]} league Best regular player s21/22"></img>`,
        bestRegPlayer_2223: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[1]} league Best regular player s22/23"></img>`,
        bestRegPlayer_2224: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[1]} league Best regular player s23/24"></img>`,
        round1_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 1 s21/22"></img>`,
        round1_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 1 s22/23"></img>`,
        round1_2324: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 1 s23/24"></img>`,
        round2_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 2 s21/22"></img>`,
        round2_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 2 s22/23"></img>`,
        round2_2324: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 2 s23/24"></img>`,
        round3_2122: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[1]} league Round 3 s21/22"></img>`,
        round3_2223: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[1]} league Round 3 s22/23"></img>`,
        round3_2324: `<img src="../img/cups/clap-b.svg" title="Shadow ${leagues[1]} league Round 3 s23/24"></img>`,
    }),
];

let managers = [
    {
        name: "Sousse Sousse",
        country: countries[0],
        achievement: [achievements[0].top1_2324, achievements[0].round3_2223],
    },
    {
        name: "whiplash 92",
        country: countries[0],
        achievement: [
            achievements[0].top2_2324,
            achievements[0].bestRegPlayer_2224,
            achievements[0].round1_2223,
            achievements[0].top3_2122,
        ],
    },
    {
        name: "El Guerrero",
        country: countries[1],
        achievement: [achievements[0].top3_2324],
    },
    {
        name: "Max Bumble",
        country: countries[0],
        achievement: [achievements[1].top1_2324],
    },
    {
        name: "Сергей Стрельченко",
        country: countries[1],
        achievement: [achievements[1].top2_2324],
    },
    {
        name: "Yoze Marino",
        country: countries[7],
        achievement: [achievements[1].top3_2324],
    },
    {
        name: "Feel Good",
        country: countries[1],
        achievement: [
            achievements[0].round1_2324,
            achievements[0].top1_2223,
            achievements[0].top2_2122,
        ],
    },
    {
        name: "Cole CaufieldTeamNePobedim",
        country: countries[2],
        achievement: [achievements[0].top1_2122],
    },
    {
        name: "Sumzair San",
        country: countries[0],
        achievement: [achievements[1].top1_2223],
    },
    {
        name: "Alex Galuza",
        country: countries[1],
        achievement: [
            achievements[0].top2_2223,
            achievements[0].bestRegPlayer_2223,
            achievements[0].round1_2122,
        ],
    },
    {
        name: "AleX TiiKii",
        country: countries[0],
        achievement: [
            achievements[0].round1_2324,
            achievements[1].top2_2223,
            achievements[0].round1_2122,
        ],
    },
    {
        name: "Nurzhan Yessengaliev",
        country: countries[2],
        achievement: [
            achievements[0].round1_2324,
            achievements[0].top3_2223,
            achievements[0].round1_2122,
        ],
    },

    {
        name: "Tandem: Vlad, whiplash 92",
        country: countries[0],
        achievement: [achievements[1].top3_2223],
    },
    {
        name: "Евгений Иванов",
        country: countries[0],
        achievement: [
            achievements[0].round1_2223,
            achievements[0].bestRegPlayer_2122,
            achievements[0].round1_2122,
        ],
    },
    {
        name: "Vladislav Belov",
        country: countries[8],
        achievement: [
            achievements[0].toxic,
            achievements[1].bestRegPlayer_2122,
            achievements[1].round1_2122,
        ],
    },
    {
        name: "Max Trufanov",
        country: countries[4],
        achievement: [achievements[0].round1_2223, achievements[0].round3_2122],
    },
    {
        name: "Евгений Медведев",
        country: countries[0],
        achievement: achievements[0].round3_2324,
    },
    {
        name: "Aleks Lang",
        country: countries[0],
        achievement: [achievements[1].round3_2324],
    },
    {
        name: "Vyacheslav Shamanov",
        country: countries[0],
        achievement: achievements[0].round1_2324,
    },

    {
        name: "Sergey Kharlanov",
        country: countries[1],
        achievement: [achievements[0].round1_2223],
    },
    {
        name: "Denis Sanzharevskyi",
        country: countries[4],
        achievement: [achievements[0].round1_2122],
    },
    {
        name: "Don Georgio",
        country: countries[0],
        achievement: [achievements[1].round1_2324],
    },
    {
        name: "Юрий Shestakov",
        country: countries[0],
        achievement: [achievements[1].round1_2324],
    },
    {
        name: "Vlad V",
        country: countries[0],
        achievement: [achievements[1].round1_2324],
    },
    {
        name: "Tandem: Sergey Dorokhov, Maxim Shvetsov",
        country: countries[0],
        achievement: [achievements[1].round1_2324],
    },
    {
        name: "Павел Роевнев",
        country: countries[0],
    },
    {
        name: "Igor Kadzayev",
        country: countries[5],
    },
    {
        name: "Oleg Karandashov",
        country: countries[4],
    },
    {
        name: "Andrii Korniichuk",
        country: countries[6],
    },

    {
        name: "Dima ATC",
        country: countries[0],
    },
    {
        name: "Alex Rybakov",
        country: countries[0],
    },
    {
        name: "Femida Femida",
        country: countries[0],
    },
    {
        name: "Maxim Shvetsov",
        country: countries[0],
    },
    {
        name: "Sergey Dorokhov",
        country: countries[0],
    },
    {
        name: "Zhanabil Au",
        country: countries[2],
    },
    {
        name: "xMoneyMaker 1",
        country: countries[0],
    },
];

const table_items = document.querySelector(".table-items");

for (let key in managers) {
    table_items.innerHTML += `
<tr class="table-row">
		<th class="table-row__countries" scope="row">
		<img src="${managers[key].country}" alt="" /></th>
		<td>${managers[key].name}</td>
		<td class="table-col-right">${managers[key].achievement}</td>
</tr>`;
}
