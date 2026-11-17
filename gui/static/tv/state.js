import {$} from "./dom.js";
export const state = {query: "", installedOnly: false, draw: {group: "", genre: ""}, sortear: null, kind: "home", code: "", filter: "", items: [], systems: [], light: [], request: 0, selected: null, draft: null, busy: false, download: null, preferences: {favorites: [], theme: "dark"}, home: null};
export const collections = [["home", "Início"], ["local", "Neste PC"], ["favorites", "Favoritos"], ["systems", "Sistemas"], ["library", "Biblioteca"], ["playing", "Jogando"], ["ranking", "Ranking"], ["wishlist", "Desejados"], ["stats", "Estatísticas"], ["heavy", "ROMs pesadas"], ["light", "ROMs leves"], ["draw", "🎲 Sortear"], ["tools", "🛠 Ferramentas"], ["apps", "Apps"]];
export const cardGames = new WeakMap();
export const observedSaves = new Map();
export const badgeKey = g => g.key || (g.code ? `${g.code}:${g.romName}` : `pc:${g.id}`);
export const WISHLIST_STORES = {steam: "Steam", psn: "PlayStation", xbox: "Xbox"};
// 🎨 Texturas no PC: pacotes do catálogo deste sistema com nome parecido; instalar baixa e
// extrai como na web (/api/texturas/instalar). Importar arquivo ou link continua na web.
export const TEXTURE_SYSTEMS = {PS2: "PS2", NGC: "GC", WII: "WII", PSP: "PSP"};
export const ui = {spotlightGame: undefined, emulatorRunning: false};
