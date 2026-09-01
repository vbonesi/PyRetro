# Plano de reorganização da pasta NSW (Google Drive)

Levantamento sobre o cache de 29/08 (`rclone lsjson -R`, 154 pastas / 12.039
itens / 0,79 TB) — será atualizado (nova varredura) antes de qualquer
execução, pra não agir em cima de dado velho. **Nada foi executado ainda.**

Regra fixa: **nome de arquivo nunca muda**. Nome de pasta pode mudar. Toda
ação abaixo é mover/renomear pasta ou apagar pasta de tradução — nunca
renomeia o `.nsp`/`.nsz`/`.xci` em si.

---

## Achado crítico (mudou o plano)

17 das 34 pastas "Russian ..." **não são só tradução** — têm um **update do
jogo** (arquivo `.nsp`/`.nsz` solto, title-id terminado em `800`) largado
junto, provavelmente porque quem baixou juntou a tradução com a versão mais
nova do jogo na mesma pasta. Apagar a pasta inteira sem olhar dentro
destruiria um update de verdade (6,75 GB dos 11,78 GB nas pastas "Russian"
são update, não tradução).

**Regra adotada:** antes de apagar qualquer pasta de tradução, resgatar
(mover) pra fora dela qualquer `.nsp`/`.nsz`/`.xci`/`.xcz` solto — ele vai
pro lado do arquivo base do jogo, como se sempre tivesse estado lá. Só
depois disso a pasta de tradução (agora só com o `atmosphere/` de verdade)
é apagada.

O caso mais extremo é o **Phoenix Wright Ace Attorney Trilogy**: a pasta
"Russian Language Mod (16.09.2024)" tem, além da tradução, um update do
jogo E 3 addons que não são tradução nenhuma (savegame, dublagem em
inglês, dublagem em japonês, desbloqueio de episódios) — tudo isso resgatado
antes de apagar só o texto russo.

---

## 1. Limpeza de nome de pasta

Tira a tag de formato do dump (`[NSZ]`/`[NSP]`/`[XCI]`/`[XCZ]`) do nome de
toda pasta que não for decompor - mesma regra que já uso pra biblioteca
(`_limpa_nome_switch`). Ex: `"Hades II [NSZ]"` → `"Hades II"`.

Duas pastas com nome torto do jeito que a pasta está hoje, acho que vale
ajustar junto (fora do escopo de tradução/coletânea, mas aparece igual):
nenhuma outra encontrada além das já resolvidas na Biblioteca (Where's My
Water já foi corrigido lá).

---

## 2. Decompor as 13 coletâneas (mesmas do `library.json`, agora nos arquivos)

Duas formas físicas, dependendo de como a pasta já está organizada por
dentro:

**A. Promover subpasta** (o jogo já mora na própria subpasta - só mover pra
fora e apagar a casca vazia):

| pasta hoje | vira (nova pasta de topo) |
|---|---|
| Portal Companion Collection [NSP] | Portal + Portal 2 |
| Windjammers 1-2 [NSZ] | Windjammers + Windjammers 2 |
| Turrican 1-3 [NSP] | Turrican Flashback + Turrican Anthology Vol. 1 + Vol. 2 |
| Shovel Knight 1-7 [NSZ] | Shovel Knight Dig + Pocket Dungeon + Treasure Trove |
| Pokemon Lets Go Eevee+Pikachu+Quest+TournamentDX [NSP] | Pokémon Let's Go Pikachu/Eevee + Pokémon Quest + Pokkén Tournament DX |
| Touhou Project for Nintendo Switch [NSZ] | 19 pastas, uma por jogo (nomes já limpos na Biblioteca) |
| Demons of Asteborg, Astebros, Kingdom [NSZ] | Demons of Asteborg + Astebros (ver nota abaixo sobre "Kingdom") |

**B. Agrupar arquivo solto** (base+update+dlc do mesmo jogo estão soltos na
raiz, sem subpasta - preciso criar a subpasta e mover pelos title-ids que já
mapeei):

| pasta hoje | vira |
|---|---|
| Pikmin 1-2 [NSP] | Pikmin 1 + Pikmin 2 |
| Capcom Fighting Collection 1-2 [NSP] | Capcom Fighting Collection + Capcom Fighting Collection 2 |
| Coffee Talk 1-2-3 [NSZ] | Coffee Talk + Coffee Talk Episode 2 + Coffee Talk Tokyo |
| Final Fantasy 1-6 Bundle Remastered [NSZ] | Final Fantasy I a VI (6 pastas) |
| SEGA Ages Games Collection [NSP] | 19 pastas (Thunder Force IV cobre o duplicado regional "Lightening Force") |
| ACA NEOGEO - 108 games Collection for Nintendo Switch [NSZ] | 108 pastas |

**Caso misto — Namco [NSZ]:** já tem 3 subpastas, mas "NAMCO Museum Archive
Vol 1-2" embala 2 produtos soltos dentro dela → vira 4 no final (Namco
Museum, Archives Vol. 1, Archives Vol. 2, Namcot Collection).

**Fora do escopo, flag pra sua decisão:** dentro de "Demons of
Asteborg..." tem uma TERCEIRA subpasta, "Kingdom of Asteborg (1+2)" — é
o cartucho de compilação de verdade (título/title-id próprio,
`010047801ED8C000`), não uma cópia solta. Contém os DOIS jogos de novo, só
que empacotados juntos (0,27 GB). Não decido sozinho se isso é redundante
o bastante pra apagar - deixo listado, sua chamada.

**Coletâneas que NÃO contam** (menu interno, você já validou esse critério):
Castlevania Dominus/Advance/Anniversary Collection, Contra Anniversary
Collection, Capcom Arcade (2nd) Stadium, Mega Man Legacy/Zero ZX/X Legacy
Collection, SNK 40th Anniversary, Samurai Shodown Neogeo Collection,
WonderBoy Anniversary Collection, Yu-Gi-Oh Early Days, Mortal Kombat
Legacy Kollection e outras do mesmo tipo já mapeadas em
`docs/NSW-mapa.md`. Ficam como estão, só perdem a tag `[NSZ]`/`[NSP]` do
nome.

---

## 3. Traduções

**Mantidas (3 PT-BR + 1 exceção justificada):**

| pasta | idioma | por quê |
|---|---|---|
| Donkey Kong Country Tropical Freeze / Tradução ... PT-BR | PT-BR | — |
| Super Mario Odyssey / Tradução ... PT-BR | PT-BR | — |
| Animal Crossing New Horizons / ACNH 2.5.1 (Hotel Patch 3.0.3) | PT-BR | pasta inteira é a tradução (instalação pra console E emulador, conferido por dentro) |
| Dragon Quest X ... (JAP) / English Machine Translation | EN | jogo é exclusivo Japão/Ásia, nunca teve lançamento oficial em inglês - mantenho por causa da sua regra ("se o jogo é japonês, mantém o inglês") |

Conferi um por um se os outros jogos com tradução russa têm versão oficial
em inglês antes de decidir - Octopath Traveler 0 e os remakes de Dragon
Quest (I&II, III, VII) TÊM lançamento ocidental oficial, então não se
qualificam pra exceção.

**Apagadas, 15 pastas "limpas" (só a tradução, nada pra resgatar):**
Deltarune, Donkey Kong Country Returns HD, Final Fantasy VII, Kirby and
the Forgotten Land, Mega Man 11, Ni No Kuni, Paper Mario TTYD (#1 e #2),
Phoenix Wright "Failing Forward", Teenage Mutant Ninja Turtles, Tony
Hawk's Pro Skater 3+4, Totally Spies, Touhou Luna Nights, Triangle
Strategy, Final Fantasy Tactics (10.10.2025).

**Apagadas, 19 pastas com resgate primeiro** (update do jogo, e no caso do
Phoenix Wright também addons, saem ANTES de apagar a tradução): Baldur's
Gate/BG2, Demonschool (x2), Double Dragon Gaiden, Dragon Quest I&II,
Dragon Quest III, Dragon Quest VII, Final Fantasy IX, Final Fantasy
Tactics (18.10.2025), Final Fantasy VIII (x2), Lunar Remastered
Collection, Octopath Traveler / Octopath Traveler 0, Phoenix Wright
(16.09.2024), Pikmin 4, Pokémon Legends Z-A, Powerslave Exhumed, Super
Mario 3D All-Stars.

Total liberado: **~5 GB de tradução de verdade** (não os 12 GB que parecia
antes de separar os updates).

---

## 4. Mods (não-tradução) → subpasta `Mods/` dentro do jogo

| jogo | o que entra em `Mods/` |
|---|---|
| Pokémon Legends Z-A | HD Textures |
| DOOM + DOOM 2 Enhanced Edition | LFS Mod Featured 18 WADs (Venom) |
| Duke Nukem 3D homebrew | High Resolution Pack version (1,48 GB) |
| Octopath Traveler 0 | 3 LFS Mods (Unlocks/Fast Travel/Damage Uncapped) |
| Phoenix Wright Ace Attorney Trilogy | Addon Gamesave, Unlock All Episodes, Dublagem EN, Dublagem JP (resgatados de dentro da pasta russa antes dela ser apagada) |
| Animal Crossing New Horizons | Amiibo JSON for Emuiibo, Official Transfer Tool, Events Unlock |

Pastas de **DLC** ("2 DLC", "34 DLC" etc.) ficam onde estão - não são mod,
são conteúdo oficial pago.

---

## 5. Dumps extraídos redundantes (achado à parte, incluído a seu pedido)

12 pastas com nome de title-id (romfs solto, sem estar empacotado em
`.nsp`/`.nsz`) - comparei cada uma com o arquivo compactado que já existe
do lado:

**9 confirmadas redundantes (mesmo title-id do `.nsp`/`.nsz` já presente) →
apagar, ~2 GB:** Kirby and the Forgotten Land, Dragon Quest VII Reimagined,
Final Fantasy IX, Final Fantasy VII, Final Fantasy VIII Remastered, Live A
Live, Mario + Rabbids Kingdom Battle, Mario Kart 8 Deluxe, Metroid Dread.

**3 flagradas, NÃO incluídas no apagar automático:** as 3 pastas de
title-id dentro de "Super Mario 3D All-Stars" (`...F546000`/`002`/`003`).
Não é o padrão simples base/update - o jogo empacota 3 programas (Mario
64/Sunshine/Galaxy) sob o mesmo título, então três subpastas com
programid distintos podem ser estrutura legítima, não cópia solta.
Prefiro te mostrar antes de mexer.

---

## O que NÃO entra nessa rodada

- Renomear arquivo (regra sua, fixa).
- As coletâneas de menu interno (ver lista na seção 2).
- "Kingdom of Asteborg (1+2)" e as 3 pastas de title-id do SM3DAS - flagradas,
  aguardando sua decisão.
- Qualquer coisa fora de `NSW/` (esse plano é só essa pasta).

## Antes de executar de verdade

1. Rodar `rclone lsjson -R` de novo (o cache é de 29/08, você pode ter
   mexido em algo desde então).
2. Rodar tudo em **modo simulação primeiro** (lista o que faria, sem tocar
   em nada) - mesmo princípio do resto do projeto.
3. Sincronizar o `library.json` no final, pra `nomes_alt`/plataforma
   continuarem batendo com o nome real da pasta.
