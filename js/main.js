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
    {
        top1: `<img src="../img/cups/top1.svg" title="Shadow SK2K league-1 top1 s22/23"></img>`,
        top2: `<img src="../img/cups/top2.svg" title="Shadow SK2K league-1 top2 s21/22"></img>`,
        top3: `Shadow ${leagues[0]} league TOP3`,
        bestRegPlayer: `Shadow ${leagues[0]} league Best regular player`,
        round1: `Shadow ${leagues[0]} league Round 1`,
        round2: `Shadow ${leagues[0]} league Round 2`,
        round3: `Shadow ${leagues[0]} league Round 3`,
    },
    {
        top1: `Shadow ${leagues[1]} league TOP1`,
        top2: `Shadow ${leagues[1]} league TOP2`,
        top3: `Shadow ${leagues[1]} league TOP3`,
        bestRegPlayer: `Shadow ${leagues[1]} league Best regular player`,
        round1: `Shadow ${leagues[1]} league Round 1`,
        round2: `Shadow ${leagues[1]} league Round 2`,
        round3: `Shadow ${leagues[1]} league Round 3`,
    },
];

let seasons = {
    s2122: "21/22",
    s2223: "22/23",
    s2324: "23/24",
    s2425: "24/25",
};

let managers = [
    {
        name: "Feel Good",
        country: countries[0],
        achievement: [achievements[0].top1, achievements[0].top2],
    },
    {
        name: "Alex Galuza",
        country: countries[1],
    },
    {
        name: "Nurzhan Yessengaliev",
        country: countries[2],
    },
    {
        name: "Sumzair San",
        country: countries[0],
    },
    {
        name: "AleX TiiKii",
        country: countries[0],
    },
    {
        name: " Vlad V",
        country: countries[0],
    },
    {
        name: "whiplash 92",
        country: countries[0],
    },
    {
        name: "Vladislav Belov",
        country: countries[3],
        achievement: [achievements[0].bestRegPlayer],
    },
    {
        name: "Cole CaufieldTeamNePobedim",
        country: countries[2],
    },
    {
        name: "Sousse Sousse",
        country: countries[0],
    },
    {
        name: "Sergey Kharlanov",
        country: countries[1],
    },
    {
        name: "Евгений Иванов",
        country: countries[0],
    },
    {
        name: "Max Trufanov",
        country: countries[4],
    },
    {
        name: "Denis Sanzharevskyi",
        country: countries[4],
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
