# PyRetro — plano de evolução a partir dos launchers prontos

**08/11/2026 · Plano aprovado em conversa, sem implementação.** Nenhum código, dado ou configuração
foi alterado por este documento.

Origem: o Victor perguntou se serviços como o GGBOX valem a pena e o que o PyRetro poderia absorver
deles e de RetroBat, Batocera, EmuDeck, LaunchBox e Lemuroid. O GGBOX em si não foi examinado; a análise
partiu do que esses projetos fazem. Conclusão: absorver a **experiência** (identificação, conteúdo,
conquistas, opções, player), não o **catálogo** de ROMs.

## 1. Decisões do Victor (08/11/2026)

| Decisão | Efeito no plano |
|---|---|
| Uso **só dele**. | Sem instalador para terceiros, sem BIOS distribuída; a licença GPL do LibretroDroid/Lemuroid só importaria se algum dia o app fosse distribuído. |
| **Só Linux** (Nitro com Arch) e Android. | Windows fora do escopo; o `bonisarch-emulator` e o Flatpak continuam a camada de emulação do PC. |
| **Só os consoles que já tem** (`[systems.*]` e `[heavy_systems.*]` do `config.toml`). | Nenhum sistema novo; "Descobrir" lista apenas esses. |
| Catálogo/baixador de ROMs: ele gostaria, **para quem sabe buscar jogos novos**; depois aceitou ficar só com a **lista de desejos** e baixar à mão. | **Não será construído**: um catálogo que baixa jogos comerciais é distribuição de material protegido. Entra no lugar o item 2 (**Descobrir**: achar o que jogar e marcar "Quero jogar"). O PyRetro não baixa ROM de lugar nenhum; os arquivos continuam entrando por **Organizar**, como hoje. |
| Gostou do resto. | Itens 1 a 7 abaixo, nesta ordem. |

## 2. Ordem

| # | Item | Esforço | Depende de |
|---|---|---|---|
| 1 | Identificação por hash (DATs) e saúde do acervo | médio | — |
| 2 | **Descobrir** (lista de desejos; substitui o catálogo/baixador) | médio | 1 ajuda, não bloqueia |
| 3 | Conquistas (RetroAchievements) | pequeno/médio | 1 ajuda a casar jogos |
| 4 | Patches IPS/BPS/UPS com conferência de hash | pequeno | — |
| 5 | Mídia por jogo e coleções | médio | 1 (busca por hash) |
| 6 | Saúde e opções por sistema/jogo | médio | 1 (BIOS por MD5) |
| 7 | Protótipo do player embutido no Android (go/no-go) | grande | — |

Cada item sai em entrega própria, com testes, e passa pelas regras da seção 4. A tela nova aparece
primeiro no modo TV (PC) e depois no Android, como no roadmap "um app só".

### 2.1 Embutido × externo (estado-alvo)

"Embutido" aqui quer dizer **dentro do app do PyRetro**. Escrever emulador novo não está em jogo: o que muda é
quem abre, configura e acompanha cada coisa.

| | PC (Linux) | Android |
|---|---|---|
| Biblioteca, nuvem, saves, estatísticas, conquistas, mídia, Descobrir | **PyRetro** | **PyRetro** |
| Leves: NES, SNES, GB/GBC/GBA, Mega Drive, SMS, Game Gear, PC Engine, Arcade, N64, NDS | RetroArch **externo** (Flatpak), com opções geridas pelo PyRetro (item 6) | **Embutido** se o protótipo (item 7) der go; senão RetroArch externo, como hoje |
| PS1 | RetroArch + SwanStation **externo** | RetroArch externo; embutido só numa segunda fase, depois do go |
| PSP | PPSSPP **externo** | PPSSPP **externo** |
| 3DS | Azahar **externo** | Lime3DS/Azahar **externo** |
| PS2, GameCube, Wii | PCSX2 e Dolphin **externos** | fora do player embutido (GameCube saiu do celular em 16/10; Wii é só PC) |
| Switch | fora do PyRetro (a gestão de ROM é feita por fora, por decisão antiga) | fora |

- **PC fica externo porque** o RetroArch já dá o CRT (crt-royale), os atalhos que o Victor domina, as conquistas
  e o rewind. Embutir no PC significaria escrever um host libretro próprio (vídeo OpenGL/Vulkan, áudio, entrada,
  shaders slang, estados) e perder tudo isso. PCSX2, Dolphin, PPSSPP e Azahar são programas independentes que
  rodam melhor como estão. O PyRetro passa a ser dono da **configuração** (item 6), não do binário.
- **Android pode embutir porque** o atrito vem de depender de apps de terceiros por intent (permissão de
  arquivos, foco do G8, saves em dois esquemas). PSP e 3DS ficam fora: emuladores dedicados são muito melhores
  que núcleos libretro.

## 3. Itens

### 1. Identificação por hash e saúde do acervo

- **Base:** `core/serials.py` já baixa os DATs Redump da libretro-database (PS1, PS2, GameCube, PSP) e
  `core/covers.py` usa o DAT do FBNeo no arcade. Falta o resto: DATs No-Intro dos cartuchos e o hash das ROMs.
- **Por que:** os erros corrigidos à mão em 29/10/2026 (The Legend of Oasis cadastrado em PS sendo Saturn,
  Mario Sunshine em Wii, Pokémon Pinball japonês, CUE sem BIN) nasceram de casar por nome.
- **Passos:**
  1. Cache dos DATs em `cache/dats/` e índice hash → (sistema, nome, região). Carregar os DATs de **todos**
     os sistemas conhecidos, também os que o Victor não usa, senão uma ROM de Saturn em PS não seria notada.
  2. Hash das ROMs locais com cache por caminho, tamanho e data. Para arquivos só na nuvem, usar o MD5 que o
     Drive já informa (`rclone lsjson --hash`).
  3. Relatório somente leitura: sistema divergente do cadastro, nome diferente do DAT, não identificada
     (esperado em hack e tradução, que aparecem como "modificada", nunca como "errada"), CUE/BIN faltando,
     BIOS ausente ou com MD5 errado.
  4. Tela em Manutenção/Ferramentas; qualquer correção é uma ação por clique, jogo a jogo.
- **Cuidados:** cabeçalhos de cartucho (iNES, SMC) mudam o hash; usar os DATs sem cabeçalho quando existirem.
  CHD guarda o SHA1 dos dados no cabeçalho, não o hash do BIN do DAT; PS1/PS2 continuam por serial (já existe).
- **Pronto quando:** fixtures com DAT miniatura reproduzem os casos acima; nenhuma escrita no acervo; testes
  Python novos.

### 2. Descobrir (no lugar do catálogo/baixador)

- **Objetivo:** achar jogos novos para os consoles que ele já tem e marcá-los numa lista de desejos. O download
  é manual, fora do PyRetro.
- **Fonte:** LaunchBox Games Database, que já é baixada (`Metadata.zip`, ~185 mil jogos). Hoje o
  `build_index()` de `core/launchbox.py` guarda só capas; passa a guardar, por plataforma, nome, ano, gênero,
  desenvolvedora, sinopse e nota da comunidade com número de votos (conferir os campos no XML ao implementar).
  ScreenScraper (já configurado) complementa nota e número de jogadores.
- **Tela:** por sistema, ordenação por nota com mínimo de votos e filtros de gênero, ano e nota. O que o
  acervo já tem sai da lista; "talvez já tenha" aparece marcado.
- **Cruzamento com o acervo:** nome normalizado **e** plataforma (regra do projeto); com o item 1 pronto, por
  hash. Empate ou dúvida não é adivinhado: o jogo aparece como "talvez já tenha".
- **Ação:** "➕ Quero jogar" acrescenta uma lista de desejos de retrô (`wishlist:retro`), ao lado de PSN, Xbox
  e Steam, pelo mesmo `add_to_wishlist` aditivo (nunca remove). A saída da lista continua item a item, como
  nas outras. Em aberto: a promoção quando a ROM chega pelo Organizar é automática ou por clique?
- **Sem download:** o PyRetro não baixa ROM de lugar nenhum. Decisão de 08/11/2026: só a lista; o Victor baixa à
  mão e a ROM entra por Organizar.
- **Pronto quando:** lista por sistema funcionando offline depois do índice; marca `wishlist:retro` testada
  contra o incidente de 21/09 (colar nomes nunca apaga nada); testes de cruzamento (nome igual com
  plataforma diferente não casa).

### 3. Conquistas (RetroAchievements)

- **Hoje:** nenhuma menção no projeto.
- **Passos:** bloco `[retroachievements]` (usuário e chave da API) só no `config.toml` privado; progresso por
  jogo e jogos masterizados pela API web; casar o jogo pelo hash que o RA publica (MD5 na maioria dos
  cartuchos, regras próprias em PS1 e arcade: conferir por sistema).
- **Tela:** barra X/Y na ficha, fileira "Com conquistas", selo "masterizado" ligado aos selos e à platina de
  Estatísticas.
- **Em jogo:** já funciona no RetroArch do PC e do celular quando logado; conferir por núcleo (SwanStation
  incluso). O modo hardcore desliga estados e rewind: padrão softcore.
- **Cuidado:** a chave nunca aparece em log, relatório ou diagnóstico.
- **Pronto quando:** um jogo real do acervo mostra o progresso; testes com respostas gravadas da API.

### 4. Patches IPS/BPS/UPS

- Ferramentas → "Aplicar patch": ROM + patch geram **cópia nova**; a original nunca muda.
- Conferir o hash de origem (BPS e UPS trazem CRC32; IPS não traz, então o PyRetro pede o hash esperado ou
  avisa). Registrar no cadastro qual patch e qual origem, para poder refazer.
- Implementação própria em Python (formatos simples), sem dependência. O resultado entra por Organizar e é
  "modificada" no item 1.
- **Pronto quando:** testes com patches sintéticos gerados no próprio teste, sem ROM real.

### 5. Mídia por jogo e coleções

- **Mídia:** vídeo, logo, screenshot e manual (PDF) do ScreenScraper, **sob demanda** e em cache por jogo,
  buscando por CRC/MD5/SHA1 quando o item 1 existir. A mídia que o Victor escolhe à mão (`core/tv_media.py`)
  sempre prevalece. Limite de espaço configurável; respeitar a cota diária do ScreenScraper.
- **Coleções:** filtro salvo com nome (sistema, gênero, ano, nota, situação); séries/franquias com sugestão por
  nome **só em relatório** (nada de fuzzy aplicado sozinho); "Continuar" com miniatura do estado (conferir o
  `savestate_thumbnail_enable` do RetroArch); modo vitrine opcional.
- **Pronto quando:** ficha com vídeo/logo/manual de jogos reais; coleções sobrevivem a reinício e sincronização.

### 6. Saúde e opções por sistema/jogo

- **Regra mantida:** o PyRetro não instala programas (`core/firstrun.py`); o `setup-linux-bonesi` continua o
  único instalador.
- **Saúde:** núcleo, BIOS (MD5 do item 1), controle e atalhos por sistema, só leitura, ao lado do
  `/diagnostics`.
- **Opções:** shader (CRT, nítido, LCD), rewind, proporção, auto-state e filtro por sistema e por jogo, gerando
  `config/<núcleo>/…cfg|.opt|.rmp`, com prévia e backup antes de escrever (mesmo padrão do
  `install-emulator-extras.py`). Respeitar o que cada núcleo não tem (SwanStation não tem rewind nem run-ahead).
- **Atenção ao setup:** o setup só pode mexer nas chaves que são dele, para nunca desfazer uma escolha feita
  na tela. Registrar em `PENDENTE-CONSOLIDAR.md`.
- **Pronto quando:** trocar o shader de um sistema pela tela aparece no RetroArch aberto em seguida, com backup
  feito; teste com `--appendconfig` descartável.

### 7. Protótipo do player embutido no Android (go/no-go)

- **Por quê:** as dores que apareceram em 08/11 (DuckStation exigindo "todos os arquivos", foco do G8 entre dois
  apps, saves em dois esquemas) nascem de depender de apps de terceiros por intent.
- **Protótipo em branch separada:** LibretroDroid (`GLRetroView`) com **dois** núcleos (Snes9x e mGBA) lendo a
  ROM da pasta Jogos. Medir tamanho do APK, latência de vídeo e áudio, consumo e, principalmente, o controle e o
  foco no G8. Gravar saves e estados no mesmo caminho do RetroArch (`saves/<sistema>/`) para continuarem
  sincronizando.
- **Critérios de go:** controle sem remendo no G8; saves e estados compatíveis com os do RetroArch (ou migração
  clara); tamanho aceitável (definir depois de medir); decisão sobre conquistas, porque o player próprio não
  traz o rcheevos (nas buscas de 08/11 não achei suporte no Lemuroid).
- **No-go:** fica o RetroArch por intent, como hoje. O PS1 já está resolvido assim.
- **Só depois de um go:** PS1, N64, NDS e Dreamcast, e discos CUE/CHD (exigem caminho de arquivo real).

## 4. Fora do escopo (decidido)

- Catálogo ou baixador de ROMs comerciais; raspar sites de ROM.
- Windows, instalador ou BIOS para terceiros.
- Reescrever o Android em Compose. WebView com ponte nativa só como teste opcional depois do item 7.
- Emuladores modernos pesados embutidos (Switch, PS3).

## 5. Regras que valem para todos os itens

- Simulação por padrão e `--apply` explícito; operações aditivas; nada apagado sozinho; fuzzy match só em
  relatório (princípios do README).
- Toda mudança de máquina também vai para o `setup-linux-bonesi`, com uma linha em `docs/PENDENTE-CONSOLIDAR.md`.
- `pyretro-gui` só é reiniciado com o modo TV fechado.
- Base de testes antes de começar: 477 Python e 58 JavaScript (PyRetro), 214 (setup).

## 6. Perguntas em aberto (nenhuma bloqueia o item 1)

1. "Quero jogar": a promoção para a Biblioteca quando a ROM chega é automática ou por clique?
2. Conquistas: confirmar softcore como padrão.
3. Limite de espaço para a mídia em cache.
