let leagues = ["Primary", "Second"];

let countries = [
    "../img/flags/rus.png",
    "../img/flags/bel.png",
    "../img/flags/kz.png",
    "../img/flags/vietnam.svg",
    "../img/flags/ua.png",
    "../img/flags/mexico.png",
    "../img/flags/pol.png",
];

let achievements = [
    (Primary_league = {
        top1_2122: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[0]} league TOP1 s21/22"></img>`,
        top1_2223: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[0]} league TOP1 s22/23"></img>`,
        top2_2122: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[0]} league TOP2 s21/22"></img>`,
        top2_2223: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[0]} league TOP2 s22/23"></img>`,
        top3_2122: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[0]} league TOP3 s21/22"></img>`,
        top3_2223: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[0]} league TOP3 s22/23"></img>`,
        bestRegPlayer_2122: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[0]} league Best regular player s21/22"></img>`,
        bestRegPlayer_2223: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[0]} league Best regular player s22/23"></img>`,
        round1_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 1 s21/22"></img>`,
        round1_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 1 s22/23"></img>`,
        round2_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 2 s21/22"></img>`,
        round2_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 2 s22/23"></img>`,
        round3_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 3 s21/22"></img>`,
        round3_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[0]} league Round 3 s22/23"></img>`,
    }),
    (Second_league = {
        top1_2122: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[1]} league TOP1 s21/22"></img>`,
        top1_2223: `<img src="../img/cups/top1.svg" title="Shadow ${leagues[1]} league TOP1 s22/23"></img>`,
        top2_2122: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[1]} league TOP2 s21/22"></img>`,
        top2_2223: `<img src="../img/cups/top2.svg" title="Shadow ${leagues[1]} league TOP2 s22/23"></img>`,
        top3_2122: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[1]} league TOP3 s21/22"></img>`,
        top3_2223: `<img src="../img/cups/top3.svg" title="Shadow ${leagues[1]} league TOP3 s22/23"></img>`,
        bestRegPlayer_2122: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[1]} league Best regular player s21/22"></img>`,
        bestRegPlayer_2223: `<img src="../img/cups/best-reg.svg" title="Shadow ${leagues[1]} league Best regular player s22/23"></img>`,
        round1_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 1 s21/22"></img>`,
        round1_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 1 s22/23"></img>`,
        round2_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 2 s21/22"></img>`,
        round2_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 2 s22/23"></img>`,
        round3_2122: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 3 s21/22"></img>`,
        round3_2223: `<img src="../img/cups/clap.svg" title="Shadow ${leagues[1]} league Round 3 s22/23"></img>`,
    }),
];

let managers = [
    {
        name: "Feel Good",
        country: countries[0],
        achievement: [achievements[0].top1_2223, achievements[0].top2_2122],
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
        name: "Nurzhan Yessengaliev",
        country: countries[2],
        achievement: [achievements[0].top3_2223, achievements[0].round1_2122],
    },
    {
        name: "Sumzair San",
        country: countries[0],
        achievement: [achievements[1].top1_2223],
    },
    {
        name: "AleX TiiKii",
        country: countries[0],
        achievement: [achievements[1].top2_2223, achievements[0].round1_2122],
    },
    {
        name: "Vlad V",
        country: countries[0],
    },
    {
        name: "whiplash 92",
        country: countries[0],
        achievement: [achievements[0].top3_2122, achievements[0].round1_2223],
    },
    {
        name: "Tandem: Vlad, whiplash 92",
        country: countries[0],
        achievement: [achievements[1].top3_2223],
    },
    {
        name: "Vladislav Belov",
        country: countries[3],
        achievement: [
            achievements[1].bestRegPlayer_2122,
            achievements[1].round1_2122,
        ],
    },
    {
        name: "Cole CaufieldTeamNePobedim",
        country: countries[2],
        achievement: [achievements[0].top1_2122],
    },
    {
        name: "Sousse Sousse",
        country: countries[0],
        achievement: [achievements[0].round2_2223],
    },
    {
        name: "Sergey Kharlanov",
        country: countries[1],
        achievement: [achievements[0].round1_2223],
    },
    {
        name: "Евгений Иванов",
        country: countries[0],
        achievement: [
            achievements[0].bestRegPlayer_2122,
            achievements[0].round1_2122,
            achievements[0].round1_2223,
        ],
    },
    {
        name: "Max Trufanov",
        country: countries[4],
        achievement: [achievements[0].round2_2122, achievements[0].round1_2223],
    },
    {
        name: "Denis Sanzharevskyi",
        country: countries[4],
        achievement: [achievements[0].round1_2122],
    },
    {
        name: "Евгений Медведев",
        country: countries[0],
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
        name: "Don Georgio",
        country: countries[0],
    },
    {
        name: "Andrii Korniichuk",
        country: countries[6],
    },
    {
        name: "El Guerrero",
        country: countries[1],
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
        name: "Сергей Стрельченко",
        country: countries[1],
    },
    {
        name: "Zhanabil Au",
        country: countries[2],
    },
    {
        name: "Юрий Shestakov",
        country: countries[0],
    },
    {
        name: "xMoneyMaker 1",
        country: countries[0],
    },
    {
        name: "Max Bumble",
        country: countries[0],
    },
    {
        name: "Yoze Marino",
        country: countries[0],
    },
];

for (let key in managers) {
    document.querySelector(".table-items").innerHTML += `
<tr class="table-row">
		<th class="table-countries" scope="row">
		<img src="${managers[key].country}" alt="" /></th>
		<td>${managers[key].name}</td>
		<td class="table-col-right">${managers[key].achievement}</td>
</tr>`;
}
