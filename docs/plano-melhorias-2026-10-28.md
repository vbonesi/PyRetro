# PyRetro — plano de melhorias para executar com o Claude

**28/10/2026 · Proposta, sem implementação ou migração aplicada.**

Objetivo: unificar web, modo TV e Android e transformar o PC em uma biblioteca local sob demanda, independente da pasta do Insync, com o Drive como acervo remoto gerido pelo PyRetro.

## 1. Direção recomendada

| Frente | Proposta |
|---|---|
| Interface | Corrigir Sortear, reduzir cabeçalho/filtros, incluir ícones de sistemas em todas as superfícies e diferenciar foco de seleção. |
| Ranking | Nota 11 dourada; escala gradual vermelho→verde, entrando no verde entre 6,5 e 7; três jogos em destaque no topo e demais abaixo. |
| Marca | Monograma PR com play em negativo; uma fonte vetorial para navegador, TV, desktop/Steam e Android. |
| PC | Raiz exclusiva `~/Games/PyRetro/`, preservando as outras instalações de Games. |
| Seleção local | Manter iniciados não finalizados e escolhas explícitas de manter baixado; apresentar prévia antes de retirar qualquer cópia. |
| NSW | Download final em `~/Downloads/NSW/<título ou volume>/`, com base/update/DLC juntos; uma pasta por título instalável. |
| Celular | Reaproveitar `Jogos/<sistema>` e `RetroArch`, aplicando a mesma gestão sem reorganização cosmética. |
| Exclusão | Ações distintas para remover deste dispositivo, enviar cópia do Drive à lixeira e remover de ambos. Saves e cadastro permanecem por padrão. |

Este plano complementa a auditoria de 28/10. Não reabre sua investigação nem incorpora suas correções como melhorias novas. AUD28-02 (pendência sem base), AUD28-03 (CUE incompleto) e AUD28-04 (colisão de faixas) precisam estar resolvidos antes das operações reais correspondentes. AUD28-01 e AUD28-07 continuam na frente de publicação/documentação. Melhorias visuais podem avançar em paralelo a essa fila.

## 2. Base verificada

Código consultado: `721b9be7c3c3c9634acbc20b1adf940b434ea47c`.

- **Sortear:** `tv.js:render()` atribui `className: "game draw"`; `.game` zera padding e alinha à esquerda. O botão está herdando o layout de capa.
- **Notas:** a web já tem `logic.js:notaColor()`. O modo TV usa selos genéricos em `fillBadges()`, sem aplicar essa distinção.
- **Sistemas:** siglas/emoji e nomes longos resultam em cartões pouco reconhecíveis e com alturas visuais diferentes.
- **Identidade:** favicon com controle roxo, TV com estrela em círculo, Android com estrela menta e instalador desktop com `applications-games`.
- **PC:** configuração ativa consultada por `retrosync.load_config()` aponta ROMs, capas, saves, estados, runtime, backups e Biblioteca para `~/Drive/Jogos`. Staging do rclone aponta para Downloads.
- **Games já existe e contém outras instalações.** Criar subpasta própria, sem limpar ou reorganizar os diretórios alheios.
- **Lançador:** o `bonisarch-emulator` instalado só aceita ROMs dentro de `~/Drive/Jogos/ROMs`. A migração depende do setup além da configuração do PyRetro.
- **Saves:** `core/drive_pending.py` depende do Insync para trazer `.pyretro-pending`; `core/mobile_sync.py` deriva os grupos PSP/3DS da pasta de saves.
- **Celular por ADB:** PyRetro **0.14.0/code 22** instalado; concessões locais de `Jogos` e `RetroArch`; pastas por sistema em Jogos e saves/states/playlists em RetroArch.
- **Android já implementa** conta Google, fila, downloads em segundo plano, fixados, bundles e saves via Drive. Evoluir esses recursos, sem recriá-los. O organizador Android atual opera os Downloads do notebook.

Verificações somente de leitura: nenhum jogo iniciado, conteúdo de save/ROM aberto, arquivo sincronizado, APK instalado ou configuração de tela/USB alterada. Pares do FolderSync e seleção atual do Insync não foram conferidos; entram no levantamento da migração. Documentos antigos contêm estados superados: a versão observada e o código prevalecem sobre descrições antigas de pendências.

## 3. Interface

### 3.1 Sortear

- Área própria com resumo dos filtros, quantidade elegível e botão **Sortear jogo**. Usar componente de ação com ícone/texto centralizados, padding e altura explícitos; não usar `.game`.
- Resultado com capa, plataforma, disponibilidade, próxima ação e **Sortear novamente**. Não lançar jogo ou download automaticamente.
- Seleção vazia, consulta falhou e sorteio em andamento são estados distintos. Manter proteção contra resposta atrasada e duplo clique.
- Preservar grupo/gênero ao voltar da ficha e restaurar foco no resultado ou botão.
- Depois: filtros opcionais **Só prontos neste dispositivo**, **Não finalizados** e evitar últimos sorteados. Não mudar silenciosamente o peso do sorteio.

**Aceite:** antes/depois do sorteio, título longo, zero resultados, erro de rede, retorno da ficha; mouse/toque/teclado/controle; 390 px, 1280×720 e 1920×1080.

### 3.2 Ícones de sistemas, consoles e lojas

Criar registro único, por exemplo `assets/platforms/manifest.json`, com ID canônico, aliases, nome curto/completo e recursos claro/escuro. Gerar a representação Android na compilação. Os nomes de módulos novos neste plano são propostas.

- Usar logos reconhecíveis ou silhuetas de consoles em conjunto visual coerente, local e offline. Registrar origem/licença em `THIRD_PARTY_NOTICES.md`; usar desenho próprio quando não houver recurso redistribuível adequado. Vetores sanitizados, sem scripts/referências externas.
- Separar plataforma de loja e emulador: Steam não é console; PlayStation precisa manter PS3/PS4; Arcade não é sinônimo de FBNeo.
- Resolver aliases por tabela, sem fuzzy. Não renomear códigos persistidos ou IDs de jogos para melhorar a apresentação.
- Caixa visual fixa, proporções preservadas, ícone + nome curto. Nome completo acessível na ficha; fallback neutro + nome quando faltar arte.
- Cobrir Sistemas, Biblioteca, Jogando, Ranking, Favoritos, Desejados, busca, sorteio, detalhes, fileiras iniciais, fila, espaço, Stream e listas equivalentes na web/Android.

**Aceite:** todo sistema retornado pelo catálogo tem recurso ou fallback, inclusive aliases; aparência clara/escura, offline, nomes longos e leitura acessível sem anunciar o nome duas vezes.

### 3.3 Ranking: cor comum e pódio

Contrato compartilhado por JS/Kotlin, com as mesmas amostras de referência:

| Nota | Cor no tema escuro | Tratamento |
|---|---|---|
| 0–1 | `#ED6A6A` | Vermelho; preservar o 0 já aceito. |
| 4 | `#E99B56` | Laranja. |
| 6,5 | `#D4BC63` | Amarelo/oliva, ainda sem verde predominante. |
| 7 | `#95C878` | Verde claro inequívoco. |
| 10 | `#66D29B` | Verde pleno. |
| 11, exatamente | `#F1C75B` | Dourado com símbolo/texto especial. |
| Sem nota | Neutro | Nunca equivale a zero. |

Interpolar RGB linearmente entre 1→4→6,5→7→10, com arredondamento idêntico nos clientes. Valores válidos entre 10 e 11 continuam visíveis e usam o verde de 10; só 11 é dourado. Não regravar nem arredondar dados existentes. Exibir vírgula decimal. No tema claro, ajustar luminosidade dos tokens para contraste mantendo as faixas.

Aplicar a nota também nas fichas, cartões, sorteio e estatísticas. Usar cor no selo/marcador, sempre com número; progresso e foco têm semânticas próprias. Verificar contraste sobre o fundo real e não depender só da cor.

**Pódio:** até três jogos no topo, demais embaixo, sem duplicação dos registros. Em tela larga, composição 2–1–3 com primeiro maior e navegação previsível; em retrato, ordem 1–2–3 com cartões legíveis. Dourado corresponde à nota 11, não à posição.

**Empates:** ordenar por nota decrescente e, inicialmente, por nome normalizado, plataforma e ID estável. Indicar “mesma nota”, sem inventar preferência do Victor. Se houver quatro jogos com 11, três entram no destaque e o quarto permanece dourado abaixo, com empate indicado. O desempate alfabético não significa avaliação superior. Ordem pessoal entre empatados pode ser recurso posterior, separado da nota.

Aplicar filtros/busca antes do pódio; título **Top 3 desta seleção**. Tratar zero/um/dois jogos e capa ausente; preservar foco por identidade ao atualizar.

**Aceite:** nulo, 0, 1, 4, 6,4, 6,5, 6,9, 7, 10, 10,5 e 11; mais de três empatados; filtros; retorno da ficha; mesma ordem e cores nos três clientes; renderização não modifica dados.

### 3.4 Outras melhorias evidentes nas imagens

1. **Mais área para jogos:** filtros secundários recolhíveis com contagem ativa; busca/seleção principal sempre claras. Hoje o cabeçalho ocupa grande parte da tela.
2. **Fileiras acessíveis:** setas e indicação de continuidade; item focado rola para dentro da área visível. Corrigir abas cortadas no começo. Não esconder scroll sem alternativa.
3. **Rodapé compacto:** ajuda contextual expansível, sem cobrir o último cartão. Mensagem de sessão encerrada dispensa-se após tratamento e não permanece em todas as abas.
4. **Glifos do controle:** a captura mostra controle Sony com instruções A/B/X/Y. Detectar layout PlayStation/Xbox/genérico, com escolha manual; não mudar bindings. Nome técnico do hardware fica em diagnóstico.
5. **Cartões regulares:** alinhar título, plataforma e selos; preservar capas; usar nomes curtos para sistemas. Foco e aba selecionada precisam de sinais diferentes.
6. **Disponibilidade compreensível:** Neste PC / Neste celular / No Drive / Transferindo / Incompleto / Origem não verificada. Rede indisponível não é biblioteca vazia.
7. **Contexto preservado:** filtros por coleção, retorno à posição anterior e Limpar filtros visível. Não transportar filtro de Ranking para Desejados acidentalmente.

## 4. Identidade visual

**Proposta:** monograma PR com play em negativo. O P identifica o nome, a perna diagonal sugere R e o triângulo interno remete a iniciar. Forma própria, sem depender de controle genérico ou marca de console.

Arquivos de estudo: [símbolo vetorial](design/pyretro-logo-proposta.svg) e [prancha de aplicações](design/pyretro-identidade-proposta.svg). São propostas ainda não instaladas.

- Base `#11212E`, menta `#81E1CA`, texto `#EDF4FD`; conservar familiaridade com o app. Dourado reservado à nota 11.
- Símbolo isolado, assinatura horizontal PyRetro, monocromático e reverso. Em 16/24 px, variante simplificada alinhada à grade; sem texto no favicon.
- Uma matriz gera SVG/ICO/PNG de navegador, tamanhos Linux/Steam, marca web/TV, Android adaptativo e monocromático. Não redesenhar cada destino à mão.
- Android com primeiro plano/fundo e área segura, testando máscaras: [documentação de ícones adaptativos](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive).
- Atualizar `tools/install_tv.py`, `.desktop` e o atalho Steam existente sem alterar appid/vínculo ou duplicar atalhos. Manter assinatura/package ID Android.
- Centralizar paleta, tipografia, raios, espaçamento, foco e selos. Não reescrever frameworks junto com a identidade.

**Aceite:** reconhecimento em todas as superfícies, 16/24/32/48/192/512 px, máscaras e temas; aprovação estética do Victor antes de substituir os ícones instalados.

## 5. PC: armazenamento independente do Drive

### 5.1 Estrutura proposta

```text
~/Games/                          # outras instalações preservadas
└── PyRetro/
    ├── ROMs/<sistema>/<jogo ou conjunto>
    ├── BIOS/                     # somente conteúdo já utilizado/mapeado
    ├── Saves/
    │   ├── saves/<sistema>/       # RetroArch
    │   ├── states/<sistema>/
    │   ├── runtime-logs/
    │   ├── PPSSPP/SAVEDATA/
    │   ├── PPSSPP/PPSSPP_STATE/
    │   ├── Lime3DS/sdmc/          # nome legado preservado por compatibilidade
    │   └── <outros emuladores já usados>/
    ├── Capas/
    ├── Midia/
    ├── Texturas/
    ├── Biblioteca/               # banco principal; etapa própria
    ├── Backups/
    ├── Importar/
    └── .pyretro/                 # manifestos, fila, recibos e staging

~/Downloads/NSW/
├── <título ou volume>/            # base + updates + DLC; destino final
└── .pyretro-partials/             # ignorado pelo organizador
```

Credenciais ficam em locais privados apropriados, fora dessa árvore de conteúdo e dos relatórios. Configurações de emuladores podem continuar nos perfis normais. Não copiar indiscriminadamente NAND/conteúdo/chaves para Saves.

O código do projeto pode permanecer na pasta atual. Retirar do Insync somente categorias de conteúdo migradas; não desmarcar `Jogos` inteiro levando o checkout junto por acidente.

### 5.2 Modelo de dados

Separar três identidades: **jogo no catálogo** (ID estável, edição/histórico), **arquivo ou conjunto remoto** (conta/pasta, IDs Drive, versão, tamanho/checksum e dependências) e **instalação local** (dispositivo, raiz, caminho relativo, integridade e proteção).

Remover uma instalação não remove o jogo. Caminho/nome não é identidade principal. Não mesclar regiões, versões ou hacks por semelhança. Compartilhamentos de faixas/arquivos devem ser explícitos.

Criar resolvedor único de destinos para catálogo, organizar, baixar, jogar, espaço e excluir. NSW é política própria, com destino final Downloads/NSW. Hoje pertence à Biblioteca: não incluí-lo no mapa de ROMs executáveis só para habilitar download.

### 5.3 Downloads e publicação

- Downloads diretos para Games, com fila persistente, pausa/retomada, cancelamento, limite de concorrência e recibo de integridade. Reutilizar o contrato de bundles.
- Staging no mesmo filesystem do destino quando depender de rename atômico; staging separado para NSW. Não pressupor que Games e Downloads estão no mesmo volume.
- Conferir espaço para parcial/destino/versão anterior. Marcar pronto só após todas as dependências; publicar descritor CUE/M3U por último. Ignorar arquivos em download e `.part`.
- ROM nova importada localmente recebe **Publicar no Drive**; versão alterada recebe **Atualizar versão no Drive**, com prévia. Manter local até envio verificado. A API oferece [uploads retomáveis](https://developers.google.com/workspace/drive/api/guides/manage-uploads).
- Versão remota diferente não substitui ROM local silenciosamente: mostrar diferença e oferecer atualização, preservando relação com edição/região/saves.
- Não usar espelhamento/`sync` nem ausência local como ordem de exclusão. Listagem falhou não é pasta vazia; mostrar data do catálogo offline.

### 5.4 Saves: dependência para retirar o Insync

Hoje o Insync transporta pendências do celular ao PC. Implementar transporte direto, preservando `docs/drive-saves.md`:

- Primeira entrega recomendada: PC como conciliador; Android envia versões imutáveis pendentes quando não consegue publicação segura. PC busca essas pendências diretamente no Drive. Com PC desligado: “Enviado ao Drive; aguardando conciliação no PC”, sem fingir atualização da versão ativa.
- Baseline por conta/pasta/grupo/dispositivo; comparação por hash, histórico e conflitos explícitos. Não usar apenas mais-recente-vence.
- Revalidar origem/destino e fechar emuladores antes de aplicar. Concorrência preserva versões. `files.version` não é CAS; GET+PATCH não garante exclusividade, como já estabelece o contrato do projeto.
- Manter pendência remota até publicação/histórico/recibo confirmados. Reprocessamento idempotente; falha não avança baseline nem apaga a única cópia.
- Sincronização manual primeiro; opção automática antes/depois da sessão só após homologação, com situação clara e tratamento de conflito.
- Mapear RetroArch, DuckStation, PCSX2, Dolphin, PPSSPP e Azahar conforme uso real. Memory card compartilhado não pode ser removido como se pertencesse a um único jogo.
- Conciliação entre dispositivos sem depender do PC fica como fase posterior, exigindo protocolo concorrente comprovado. Downloads e jogos locais não precisam esperar essa evolução.

### 5.5 Biblioteca, capas e backups

ROMs podem sair primeiro do Insync. As demais categorias só saem quando suas responsabilidades tiverem substituto:

- Banco principal local, lock e escrita atômica, IDs/campos preservados; snapshot remoto versionado/restaurável, um escritor principal nesta fase. Android mantém catálogo e fila, sem escrever o JSON principal diretamente.
- Capas/mídia em cache com versão remota; remover ROM não apaga capa/histórico.
- Backup local e remoto verificável; backup na mesma unidade não cobre falha dela. Retenção explícita e visível, sem expurgo automático introduzido pela migração.
- Runtime transferido como arquivo, sem somar novamente logs ao tempo existente; IDs idempotentes de sessão evitam duplicação PC/Android.

## 6. Exclusão local e na nuvem

| Ação | Efeito | Preserva por padrão |
|---|---|---|
| Remover deste PC/celular | Instalação selecionada e membros exclusivos. | Drive, outro dispositivo, saves/estados, texturas, capa, cadastro, nota e tempo. |
| Enviar cópia do Drive à lixeira | IDs remotos apresentados na prévia; não remove cópia local. | Local, saves e histórico do jogo. |
| Remover local e enviar Drive à lixeira | Duas operações com resultados individuais. | Saves e cadastro. |
| Remover cadastro | Administração separada da liberação de espaço. | Não implica apagar arquivos. |

Usar a lixeira como padrão para “apagar na nuvem”, não exclusão permanente. O Drive documenta [recuperação por até 30 dias](https://developers.google.com/workspace/drive/api/guides/delete); explicar prazo e não prometer retenção indefinida/liberação imediata de quota.

Contrato da operação:

1. Prévia com escopo, dispositivo/conta, jogo, arquivos, bytes, dependências e cópias conhecidas restantes. Cliente não fornece caminho absoluto arbitrário.
2. Preservar faixas de CUE/M3U/GDI usadas por outros descritores. NSW opera por título/volume instalável; coletânea pode corresponder a vários jogos na Biblioteca, todos mostrados na prévia.
3. Bloquear durante execução/transferência; fixado exige retirada explícita da proteção. Avisar se for a última cópia conhecida ou a origem não estiver confirmada.
4. Confirmação com local/Drive por extenso; sem checkbox persistente que amplie escopo. Ação remota exige rede, origem validada e capacidade de escrita. Não executar exclusão enfileirada offline sem revalidação.
5. Revalidar IDs/manifesto/versões antes de agir; mudança invalida prévia. Registrar cada item e recuperar falha parcial: lote remoto não é atômico.
6. Atualizar índices/recibos. Remoção remota intencional não dispara reupload automático da cópia local restante. Cadastro continua com nova disponibilidade.

Conferir escopo OAuth real: leitura pelo rclone não comprova capacidade de publicar/trash. No Android, SAF local e API Drive são capacidades distintas. Reusar autorizações suficientes; renovar apenas quando necessário.

## 7. Android

Manter Jogos e RetroArch. O [SAF](https://developer.android.com/training/data-storage/shared/documents-files) usa concessões para a localização escolhida; mudanças de árvore podem exigir novos vínculos. A equivalência desejada é de gestão, não de nomes de pastas idênticos ao Linux.

- Reusar fila/checkpoints/fixados/serviço/histórico; acrescentar origem, destino e estados comuns.
- Oferecer iniciados como seleção inicial protegida, por dispositivo; favorito não significa obrigatoriamente manter instalado.
- Conferir FolderSync antes de substituir sua gestão; desativar só os pares cobertos pelo PyRetro, sem apagar origem/destino.
- Renomear claramente o fluxo existente como **Organizar Downloads do notebook**. **Importar neste celular**, via seletor local, é função nova e separada.
- NSW deste pedido vai para Downloads do PC; não sugerir emulação no celular. Download NSW no telefone dependeria de pedido/destino próprios.
- Falta de espaço, Drive indisponível ou concessão expirada devem ter ação concreta. URI/caminho do PC não é caminho válido do telefone.

## 8. Migração em etapas reversíveis

1. **Inventário em leitura:** raízes, symlinks, perfis, playlists, lançador/setup, Flatpak, iniciados/fixados, variantes, bundles e colisões. Usar módulo/API para Biblioteca/configuração, sem abrir arquivos manualmente. Inventário privado fora do Git.
2. **Prévia da seleção:** `iniciado && !finalizado`, fixados e escolhas extras. Favoritos/finalizados podem ser incluídos explicitamente. Associação ausente/ambígua vai para revisão. Mostrar bytes e iniciados só na nuvem.
3. **Integridade remota:** cada conjunto cuja cópia local antiga será retirada precisa de verificação por IDs/tamanho/hash compatível; nome+tamanho não provam igualdade. Sem hash confiável, verificar conteúdo por leitura adicional. Upload incompleto bloqueia retirada.
4. **Copiar inicialmente:** criar Games/PyRetro e copiar seleção, validando hashes/manifestos. Não usar hardlinks/symlinks de ROM apontando ao Drive. Guardar recibos e backups de configuração.
5. **Piloto de ROMs:** atualizar PyRetro e lançador, perfis, permissões Flatpak e playlists; testar um leve e um conjunto pesado. Não ampliar acesso a toda a home para contornar permissão.
6. **Homologar:** abrir/jogar/sair/retornar com foco, offline, download/interrupção, remoção local em fixture. Iniciados acessíveis; NSW termina somente em Downloads/NSW.
7. **Insync/ROMs:** retirar seleção local das pastas já verificadas pela função própria do Insync. Nunca `rm` dentro do Drive como atalho para somente-nuvem. Conferir comportamento da versão instalada e objetos remotos após a operação.
8. **Saves por grupo:** emuladores fechados; copiar/verificar todos os saves, inclusive jogos sem ROM local; atualizar perfis/baselines e testar ida/volta PC↔Drive↔Android. Só então desativar o grupo no Insync/FolderSync.
9. **Metadados/backups:** migrar cada categoria quando publicação/restauração direta existir. Não desligar tudo enquanto algum consumidor depender do Insync.
10. **Encerrar:** registrar raízes, seleção, testes reais, adiamentos e rollback. Retirar redundâncias só após revisão. Outras pastas de Games e Downloads permanecem fora do plano.

**Rollback:** restaurar apontamentos/permissões, preservando dados novos em Games; reconciliar saves antes de voltar. Não sobrescrever save novo com snapshot antigo nem religar dois gravadores concorrentes do mesmo grupo.

## 9. Entregas para o Claude

| Etapa | Conteúdo | Pontos de código/integração | Aceite |
|---|---|---|---|
| A | Sortear, filtros, rodapé, foco, glifos | `gui/static/tv.*`, testes de interface | Problemas das quatro capturas resolvidos nos tamanhos-alvo. |
| B | Plataformas e ícones | Novo manifesto/assets; `app.js`, `tv.js`, Android | Todas as ocorrências coerentes, offline e fallback. |
| C | Cor de nota e pódio | `logic.js`, `tv.js`, estilos, `GridRules.kt`, `MainActivity.kt` | Mesmos limites/empates/filtros; dados preservados. |
| D | Identidade aprovada | SVG fonte, geração, favicon, instalador, Android | Marca comum e atalhos existentes atualizados. |
| E | Modelo de armazenamento e simulação | Configuração/resolvedor; `core/{tv,play,heavy_roms,mobile_roms,organize,library}.py`; setup | Prévia completa de destinos/dependências/colisões; NSW separado; sem mover dados. |
| F | Transferência e remoção | Adaptador Drive, fila, preview/apply, UI de espaço | Download/upload/trash recuperáveis e idempotentes. |
| G | Saves diretos e backups | `drive_saves.py`, `drive_pending.py`, `mobile_sync.py`; `GoogleDrive.kt`, `DriveSaves.kt`, `FileSync.kt` | Pendências sem Insync, conflitos/recibos após falha, restauração verificada. |
| H | Migração real por categoria | Configuração, setup, Insync/FolderSync | Prévia aprovada, iniciados preservados e evidência real antes de retirar cada sincronização. |

E→F→piloto de ROMs pode avançar antes de G; **retirar Saves do Insync depende de G**. A–D independem da migração. Entregas pequenas, sem misturar aparência, operações reais e auditoria no mesmo commit. Atualizar READMEs com estado atual curto e histórico separado.

### Validação

- Interface: `tests/test_app.html`/`window.RESULTADO`; web/TV em 390/720p/1080p, temas e entradas; Android retrato/paisagem, fonte ampliada, retorno do emulador.
- Regras: `python3 -m unittest discover -s tests`; regressões úteis para destinos, symlinks/travessia, bundles compartilhados/incompletos, colisão, origem alterada, espaço insuficiente, interrupção, ausência remota e execução repetida.
- Android alterado: `tools/build_android.py` com toolchain documentado, JVM/build/lint e instrumentação pertinente. Assinatura preservada; instalação sempre `adb install --user 0 -r`, celular por um agente de cada vez.
- Migração: fixtures com duas raízes independentes/falso Drive, depois piloto real. Testes sintéticos não homologam G8, rede, Insync ou emuladores. Nunca assumir que save real é descartável.
- Esta entrega documental: conferir referências, XML/renderização e diff; não alegar repetição dos testes do produto.

## 10. Prompt para começar com o Claude

> Leia `docs/trabalho-em-conjunto.md` e este plano. Execute as melhorias em entregas pequenas, começando por A–C, sem migrar/remover arquivos reais na primeira entrega. Preserve a auditoria como frente própria e respeite seus bloqueios antes das operações correspondentes. Prepare D a partir do estudo vetorial e mostre as aplicações antes de substituir ícones instalados. Depois implemente E–G com fixtures e gere a prévia H: Games/PyRetro para o acervo local, NSW em Downloads/NSW, iniciados mantidos, remoção local e lixeira do Drive separadas, saves/cadastro preservados. Não desative Insync/FolderSync nem aplique migração real antes de apresentar destinos, cópias verificadas, conflitos e rollback para minha decisão. Não abra library.json/config.toml manualmente nem publique inventários/credenciais. Documente o que realmente entregou e distinga testes sintéticos de homologação real.
