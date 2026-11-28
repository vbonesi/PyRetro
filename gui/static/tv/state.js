import {$} from "./dom.js";
export const state = {query: "", installedOnly: false, draw: {group: "", genre: ""}, sortear: null, kind: "home", code: "", quick: "all", order: "", system: "", filter: "", roda: "", items: [], systems: [], light: [], request: 0, selected: null, draft: null, busy: false, download: null, preferences: {favorites: [], theme: "dark"}, home: null};
export const collections = [["home", "Início"], ["library", "Biblioteca"], ["wishlist", "Desejados"], ["apps", "Apps e stream"], ["tools", "Ferramentas"], ["stats", "Estatísticas"], ["draw", "🎲 Sortear"]];
export const cardGames = new WeakMap();
export const observedSaves = new Map();
export const badgeKey = g => g.key || (g.code ? `${g.code}:${g.romName}` : `pc:${g.id}`);
export const WISHLIST_STORES = {steam: "Steam", psn: "PS4", xbox: "Xbox", switch: "Switch", switch2: "Switch 2"};
// 🎨 Texturas no PC: pacotes do catálogo deste sistema com nome parecido; instalar baixa e
// extrai como na web (/api/texturas/instalar). Importar arquivo ou link continua na web.
export const TEXTURE_SYSTEMS = {PS2: "PS2", NGC: "GC", WII: "WII", PSP: "PSP"};
// Plataformas do Victor na ordem de prioridade do card (core/onde_roda.py): Switch e PS4 primeiro.
export const RODA = [["switch", "Switch"], ["ps4", "PS4"], ["xbox", "Xbox"], ["pc", "PC"], ["switch2", "Switch 2"]];
export const rodaOf = g => RODA.filter(([id]) => g.tracking?.onde_roda?.[id]?.existe === true);
// Valor do filtro "Onde roda": "" (qualquer), "quero" (quero jogar) ou o id de uma plataforma.
export const rodaMatch = (g, value) => !value || (value === "quero" ? g.tracking?.jogar?.estado === "quero" : g.tracking?.onde_roda?.[value]?.existe === true);
export const ui = {spotlightGame: undefined, emulatorRunning: false};
