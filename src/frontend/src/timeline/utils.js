/* eslint-disable no-bitwise */

import { MONTHS_PER_YEAR } from "./constants";

export const fill = n => {
  const arr = [];
  for (let i = 0; i < n; i += 1) {
    arr.push(i);
  }
  return arr;
};

// https://coolors.co/palette/03045e-023e8a-0077b6-0096c7-00b4d8-48cae4-90e0ef-ade8f4-caf0f8
// https://coolors.co/palette/dad7cd-a3b18a-588157-3a5a40-344e41
// https://coolors.co/palette/f08080-f4978e-f8ad9d-fbc4ab-ffdab9
// https://coolors.co/palette/d9ed92-b5e48c-99d98c-76c893-52b69a-34a0a4-168aad-1a759f-1e6091-184e77
// https://coolors.co/palette/f7b267-f79d65-f4845f-f27059-f25c54
// https://coolors.co/palette/fec5bb-fcd5ce-fae1dd-f8edeb-e8e8e4-d8e2dc-ece4db-ffe5d9-ffd7ba-fec89a
const COLORS_pallettes = [
  '03045e-023e8a-0077b6-0096c7-00b4d8-48cae4-90e0ef-ade8f4-caf0f8'.split('-'),
  'dad7cd-a3b18a-588157-3a5a40-344e41'.split('-'),
  'f08080-f4978e-f8ad9d-fbc4ab-ffdab9'.split('-'),
  'd9ed92-b5e48c-99d98c-76c893-52b69a-34a0a4-168aad-1a759f-1e6091-184e77'.split('-'),
  'f7b267-f79d65-f4845f-f27059-f25c54'.split('-'),
  'fec5bb-fcd5ce-fae1dd-f8edeb-e8e8e4-d8e2dc-ece4db-ffe5d9-ffd7ba-fec89a'.split('-')
];

const COLORS = COLORS_pallettes[0];

export const randomColor = () =>
  COLORS[Math.floor(Math.random() * COLORS.length)];

let color = -1;
export const nextColor = (key) => {
  color = (color + 1) % COLORS_pallettes[key % COLORS_pallettes.length].length;
  return COLORS_pallettes[key % COLORS_pallettes.length][color];
};

export const hexToRgb = hex => {
  const v = parseInt(hex, 16);
  const r = (v >> 16) & 255;
  const g = (v >> 8) & 255;
  const b = v & 255;
  return [r, g, b];
};

export const colourIsLight = (r, g, b) => {
  const a = 1 - (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return a < 0.5;
};

export const addMonthsToYear = (year, monthsToAdd) => {
  let y = year;
  let m = monthsToAdd;
  while (m >= MONTHS_PER_YEAR) {
    m -= MONTHS_PER_YEAR;
    y += 1;
  }
  return { year: y, month: m + 1 };
};

export const addMonthsToYearAsDate = (year, monthsToAdd) => {
  const r = addMonthsToYear(year, monthsToAdd);
  return new Date(`${r.year}-${r.month}`);
};

// Credit: https://jsfiddle.net/katowulf/3gtDf/
const ADJECTIVES = [
  "adamant",
  "adroit",
  "amatory",
  "animistic",
  "antic",
  "arcadian",
  "baleful",
  "bellicose",
  "bilious",
  "boorish",
  "calamitous",
  "caustic",
  "cerulean",
  "comely",
  "concomitant",
  "contumacious",
  "corpulent",
  "crapulous",
  "defamatory",
  "didactic",
  "dilatory",
  "dowdy",
  "efficacious",
  "effulgent",
  "egregious",
  "endemic",
  "equanimous",
  "execrable",
  "fastidious",
  "feckless",
  "fecund",
  "friable",
  "fulsome",
  "garrulous",
  "guileless",
  "gustatory",
  "heuristic",
  "histrionic",
  "hubristic",
  "incendiary",
  "insidious",
  "insolent",
  "intransigent",
  "inveterate",
  "invidious",
  "irksome",
  "jejune",
  "jocular",
  "judicious",
  "lachrymose",
  "limpid",
  "loquacious",
  "luminous",
  "mannered",
  "mendacious",
  "meretricious",
  "minatory",
  "mordant",
  "munificent",
  "nefarious",
  "noxious",
  "obtuse",
  "parsimonious",
  "pendulous",
  "pernicious",
  "pervasive",
  "petulant",
  "platitudinous",
  "precipitate",
  "propitious",
  "puckish",
  "querulous",
  "quiescent",
  "rebarbative",
  "recalcitant",
  "redolent",
  "rhadamanthine",
  "risible",
  "ruminative",
  "sagacious",
  "salubrious",
  "sartorial",
  "sclerotic",
  "serpentine",
  "spasmodic",
  "strident",
  "taciturn",
  "tenacious",
  "tremulous",
  "trenchant",
  "turbulent",
  "turgid",
  "ubiquitous",
  "uxorious",
  "verdant",
  "voluble",
  "voracious",
  "wheedling",
  "withering",
  "zealous"
];
const NOUNS = [
  "ninja",
  "chair",
  "pancake",
  "statue",
  "unicorn",
  "rainbows",
  "laser",
  "senor",
  "bunny",
  "captain",
  "nibblets",
  "cupcake",
  "carrot",
  "gnomes",
  "glitter",
  "potato",
  "salad",
  "toejam",
  "curtains",
  "beets",
  "toilet",
  "exorcism",
  "stick figures",
  "mermaid eggs",
  "sea barnacles",
  "dragons",
  "jellybeans",
  "snakes",
  "dolls",
  "bushes",
  "cookies",
  "apples",
  "ice cream",
  "ukulele",
  "kazoo",
  "banjo",
  "opera singer",
  "circus",
  "trampoline",
  "carousel",
  "carnival",
  "locomotive",
  "hot air balloon",
  "praying mantis",
  "animator",
  "artisan",
  "artist",
  "colorist",
  "inker",
  "coppersmith",
  "director",
  "designer",
  "flatter",
  "stylist",
  "leadman",
  "limner",
  "make-up artist",
  "model",
  "musician",
  "penciller",
  "producer",
  "scenographer",
  "set decorator",
  "silversmith",
  "teacher",
  "auto mechanic",
  "beader",
  "bobbin boy",
  "clerk of the chapel",
  "filling station attendant",
  "foreman",
  "maintenance engineering",
  "mechanic",
  "miller",
  "moldmaker",
  "panel beater",
  "patternmaker",
  "plant operator",
  "plumber",
  "sawfiler",
  "shop foreman",
  "soaper",
  "stationary engineer",
  "wheelwright",
  "woodworkers"
];

export const randomTitle = () =>
  `${ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)]} ${
    NOUNS[Math.floor(Math.random() * NOUNS.length)]
  }`;
