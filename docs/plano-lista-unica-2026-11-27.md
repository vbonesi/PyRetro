# Plano de 27/11/2026 (noite): retrô no Drive, o resto vira lista "onde jogar"

Plano fechado com o Victor em 27/11 (noite); nada executado ainda. Marcas: **P** pesado, **L** leve, **V** Victor.

## Decisões já tomadas
- **Fica no Drive (retrô):** NES, SNES, Mega Drive, Master System, Game Gear, GB, GBC, GBA, N64, PC Engine,
  PC Engine CD e Arcade (FBNeo). Cerca de 10 GB.
- **Sai do Drive (lixeira, 30 dias para desfazer):** ROMs de PS1, PS2, PSP, DS, 3DS, GameCube, Wii e **todos** os
  dumps de Switch. Cerca de 505 GB mais a pasta NSW. **Ficam (Jogando, conferido pelo Victor):** PS2 Guitar Hero III e
  Need for Speed: Underground 2; Switch Life is Strange: True Colors, Portal 2, Squad 51 vs the Flying Saucers, Streets of
  Rage 4, Super Mario Bros. Wonder, Zelda: Breath of the Wild e Touhou Luna Nights. Os dois de PS1 em Jogando saem.
- **O card fica:** nota, tempo, finalizado, saves e sinopse continuam no banco.
- **Jogos que o Victor já tem** (Steam, Epic, GOG, Xbox, PS4 etc.) continuam separados por loja, como hoje.
- **Jogos que ele não tem** viram um card só, "Quero jogar", que mostra onde o jogo existe entre as plataformas
  dele: **Switch, PS4, Xbox Series S, PC e Switch 2** (Switch 2 só por emulação, por enquanto). Ordem de
  prioridade no card: **Switch e PS4 primeiro**, depois Xbox e PC.
- Cada plataforma mostra um **tamanho aproximado em GB** (ordem de grandeza, sem fonte).
- Se existe no PS4, o card mostra PS4 (as marcas "não" da planilha não tiram a plataforma).
- **Steam e Xbox continuam como listas de preço** (IsThereAnyDeal acompanha a Steam): o que roda no PC fica na
  lista da Steam; o PyRetro gera a lista do que falta adicionar na wishlist da Steam e na do Xbox, para o Victor
  acompanhar preço pelos dois (não há API para escrever wishlist; ele adiciona à mão).
- Quando o Victor baixa ou compra, indica no app em qual plataforma (e, se for PC, em qual loja); o card passa a
  "tenho" naquela loja.
- **Pesquisa de disponibilidade:** IGDB (plataformas e ports de cada jogo) + lojas; web só onde o IGDB falhar.
  Campo manual por plataforma ("tem/não tem", confirmado pelo Victor) vence a pesquisa.

## Fases propostas
- **F0 (L)** Cópia de segurança: retrato completo do banco pela API e manifesto (nome, tamanho, MD5, ID do Drive)
  de tudo que vai para a lixeira.
- **F1 (P)** Modelo de dados: `onde_roda` por plataforma (existe, tamanho aproximado, manual), estado
  `quero jogar`/`tenho em <loja>`, ação "baixei/comprei em…"; junção de cards repetidos entre listas; sync da Steam
  sem apagar card.
- **V0 (V)** Criar o app de desenvolvedor da Twitch para o IGDB e pôr a chave no config (não no chat).
- **F2 (P)** Pesquisa: IGDB para todos os cards fora do retrô e dos Desejados; tamanhos aproximados; relatório
  das dúvidas.
- **F3 (L)** Modo TV: selos de plataforma na ordem de prioridade, filtros "Roda no PS4/Switch/…", ação de escolher
  onde jogar. Android depois.
- **F4 (L)** Listas "falta na wishlist da Steam" e "falta na wishlist do Xbox".
- **V1 (V)** Victor revisa a lista de remoção e corrige disponibilidades à mão.
- **F5 (L)** Remoção para a lixeira do Drive (exceto a lista de Jogando acima), catálogo e índice do celular
  atualizados; sistemas fora do retrô deixam de oferecer download no PC e no Android.
- **F6 (L)** Sortear em quatro grupos; aposentar o PyRetro Shop.

## Decisões da segunda rodada
- **Sync da Steam nunca apaga card:** jogo que sai da wishlist da Steam só gera aviso.
- **Celular:** as ROMs que já estão lá ficam (o Victor apaga à mão). Daqui em diante o PC e o Android só baixam ROM retrô.
- **Sortear** em quatro grupos: jogos retrô; quero jogar que existe no Switch ou no PS4; jogos que já tenho (PS4, Xbox, PC);
  todos.
- **PyRetro Shop (Tinfoil) aposentado:** sai o índice `shop.json` do Drive, o botão e o comando; o Victor tira do SD
  `credentials.json`/`gdrive.token` e a fonte gdrive do Tinfoil.
- **Emuladores ficam** no PC e no celular (PCSX2, Dolphin, PPSSPP, Azahar, SwanStation etc.): quando não houver versão
  de Switch ou PS4, o Victor joga por eles.
