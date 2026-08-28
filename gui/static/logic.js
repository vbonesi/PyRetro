// Lógica pura da interface: nenhuma função aqui toca no DOM, faz
// requisição ou depende de estado global. Foi separada de app.js (que
// cuida de tela e eventos) justamente pra poder ser testada sem
// navegador montado - ver tests/test_app.html.
//
// Carregado ANTES de app.js no index.html.

// Cor da nota (pedido do usuário 27/08: "colocar cor nas notas,
// vermelho para 1 e verde para 10 e dourado para 11") - interpola entre
// as cores de tema já existentes (--err vermelho, --ok verde) em vez de
// vermelho/verde puros, pra combinar com o resto da UI; nota > 10
// (só 11 visto na coleção real, nota "fora da escala") usa --warn
// (dourado/âmbar, já é a cor de destaque do tema). Sem nota, sem cor
// (não decide nada por quem ainda não avaliou).
function notaColor(nota) {
  if (nota === null || nota === undefined || nota === "") return null;
  const n = Number(nota);
  if (Number.isNaN(n)) return null;
  if (n > 10) return "#e0a52c"; // --warn
  const t = Math.max(0, Math.min(1, (n - 1) / 9)); // 1 -> 0, 10 -> 1
  const from = [224, 92, 92];   // --err
  const to = [76, 175, 125];    // --ok
  const rgb = from.map((c, i) => Math.round(c + (to[i] - c) * t));
  return `rgb(${rgb.join(",")})`;
}

function notaTexto(nota) {
  if (nota === null || nota === undefined || nota === "") return "–";
  return String(Number(nota)); // 8.0 -> "8", 7.1 -> "7.1"
}

function formatGB(bytes) {
  return (bytes / (1024 ** 3)).toFixed(2) + " GB";
}

function stemOf(item) {
  if (item.is_dir) return item.name;
  const idx = item.name.lastIndexOf(".");
  return idx > 0 ? item.name.slice(0, idx) : item.name;
}

// Rótulo amigável pra fonte técnica - só exibição, não muda o dado
// (mantém "psn"/"heroic:epic"/etc no library.json, que é o que o CLI
// grava/lê). Fonte sem entrada aqui (jogo sem loja associada, veio só
// da planilha) usa a própria plataforma como agrupamento (ver
// libraryGroupsFor) em vez de um genérico "(sem fonte)" que escondia
// que aquele jogo é, por exemplo, "Arcade" ou "Xbox One" físico.
const FONTE_LABELS = {
  "steam": "Steam",
  "xbox": "Xbox",
  "psn": "PSN (digital)",
  "psn:fisico": "PSN (físico)",
  "heroic:epic": "Epic Games",
  "heroic:gog": "GOG",
  "heroic:amazon": "Amazon Games",
  // "switch" (27/08) precisa bater com o mesmo rótulo que a plataforma
  // "Nintendo Switch" já usa (jogo de planilha sem fonte cai no
  // fallback plataforma, ver libraryGroupsFor) - senão os 22 jogos
  // recém importados (fonte "switch") viravam uma aba própria
  // "switch" em vez de se juntar aos que já existiam na planilha.
  "switch": "Nintendo Switch",
};

function fonteLabel(f) {
  return FONTE_LABELS[f] || f;
}

// Fonte(s) de loja E plataforma, juntas (mudança 28/08) - antes era
// "fonte se tiver, senão plataforma", o que escondia metade da verdade
// pra jogo que o usuário tem em mais de um lugar: "A Plague Tale:
// Innocence" está com plataforma "Xbox One" (onde ele FECHOU) e fonte
// "heroic:epic" (onde também é dono), e só aparecia na aba Epic - o
// Xbox, que é onde o progresso aconteceu, ficava de fora. Mesmo caso de
// Overcooked/The Escapists 2/Mortal Kombat X. Agora aparece nas duas,
// que é o que reflete a realidade. Rótulo repetido é deduplicado em
// libraryTabGroupsFor.
function libraryGroupsFor(g) {
  return [...new Set([...g.fontes, g.plataforma])];
}

// Curadoria manual de agrupamento pra NAVEGAÇÃO (sub-abas) - nunca
// mexe no dado gravado (plataforma do card continua mostrando o
// modelo exato), só junta grupo quase-duplicado pra não poluir a
// barra de abas. Pedido do usuário 27/08: "unir iOS e Android em
// Mobile" + "curar melhor Xbox, pois tem só Xbox e lá tem por modelo e
// tem os outros separados, series, 360 e one" - 4 variações de Xbox
// (fonte "xbox" + plataforma "Xbox 360"/"Xbox One"/"Xbox Series S")
// viram uma aba só. Aplicado sobre o RÓTULO amigável (pós-fonteLabel),
// não sobre a chave técnica - por isso funciona pra fonte E plataforma
// ao mesmo tempo (ambas já viraram rótulo antes de chegar aqui).
const GROUP_TAB_ALIASES = {
  "iOS": "Mobile",
  "Android": "Mobile",
  "Xbox 360": "Xbox",
  "Xbox One": "Xbox",
  "Xbox Series S": "Xbox",
  // Mesma loja com dois nomes (plataforma gravada vs rótulo da fonte)
  // - sem isso a união fonte+plataforma (ver libraryGroupsFor) criaria
  // duas abas pro mesmo lugar.
  "Epic Games Store": "Epic Games",
  "PSN (PS4)": "PSN (digital)",
  "PSN (PS5)": "PSN (digital)",
  "PSN físico (PS4)": "PSN (físico)",
};

// Rótulos que descrevem COMO o jogo é possuído, não ONDE ele está -
// aparecem no card, mas nunca viram aba própria (correção 28/08: o
// usuário pediu "o ideal é ter PlayStation 3 e PlayStation 4 apenas, e
// no jogo colocar a label PSN (digital) e Físico", e eu tinha deixado
// os dois virarem aba ao lado das plataformas). A informação não se
// perde: continua na linha de meta do card, ex: "PlayStation 4 · PSN
// (físico)".
const TAB_NAO_AGRUPA = new Set(["PSN (digital)", "PSN (físico)"]);

function libraryTabGroupsFor(g) {
  const labels = libraryGroupsFor(g)
    .map(f => GROUP_TAB_ALIASES[fonteLabel(f)] || fonteLabel(f))
    .filter(label => !TAB_NAO_AGRUPA.has(label));
  return [...new Set(labels)];
}

function libraryMatchesFilters(g, fonte, status, noCover, mostrarOcultos) {
  if (g.oculto && !mostrarOcultos) return false;
  if (fonte && !libraryTabGroupsFor(g).includes(fonte)) return false;
  if (noCover && g.capa) return false;
  if (status === "iniciado" && !g.iniciado) return false;
  if (status === "finalizado" && !g.finalizado) return false;
  if (status === "nao_finalizado" && g.finalizado) return false;
  if (status === "platinado" && !g.platinado) return false;
  return true;
}

// Deixa acessível pros testes (e pro app.js, que roda no mesmo escopo
// global do navegador).
if (typeof module !== "undefined" && module.exports) {
  module.exports = { notaColor, notaTexto, fonteLabel, libraryGroupsFor,
                     libraryTabGroupsFor, libraryMatchesFilters, stemOf, formatGB,
                     FONTE_LABELS, GROUP_TAB_ALIASES, TAB_NAO_AGRUPA };
}
