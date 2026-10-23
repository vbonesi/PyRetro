# Modo TV do PyRetro

Integração com Steam Big Picture, iniciada em 15/10/2026.
O modo TV já oferece lançamento de ROMs pelo `bonisarch-emulator`.

## Acesso

- Na máquina: `http://127.0.0.1:8000/tv`.
- Pelo acesso HTTPS/Tailscale já configurado: acrescentar `/tv` ao endereço do PyRetro.
- A interface normal tem um link **Modo TV**. A versão TV oferece o retorno à interface completa.

O serviço `pyretro-gui` precisa estar ativo. Não há servidor adicional nem nova porta.
A rota usa os mesmos cabeçalhos de segurança e as mutações exigem o token CSRF existente.

## Navegação

Direcional ou analógico esquerdo navegam entre os botões e as capas. A confirma e
B volta. O mapeamento segue o padrão Gamepad do navegador; teclado também funciona
com setas, Enter, Tab e Esc. Pressione um botão para o navegador reconhecer o controle.
Y abre a busca com teclado na tela (X apaga, Menu confirma e B cancela).
LB/RB pulam páginas da grade ou da fileira de capas; LT/RT trocam coleções. Page Up/Page Down também
funcionam pelo teclado. **Início** reúne recentes, continuar jogando, favoritos,
instalações Steam/Heroic e ROMs locais em fileiras, com destaque do jogo selecionado.
O foco inicial fica no botão de abrir o destaque, sem rolar a tela para fora do cabeçalho.
Sistemas mostra totais e presença local;
Neste PC reúne instalações Steam/Epic/GOG/Amazon e ROMs locais completas.
Os filtros de plataforma, gênero e Só neste PC são botões navegáveis.
A busca na tela inicial usa todo o catálogo; nas coleções, filtra a seleção atual.
Atualizar relê o disco/cache, sem sincronizar posse ou atualizar o Drive.

Mouse/toque: as fileiras têm setas com alvos de 48 px e rolagem nativa por toque
ou trackpad. A roda vertical sobre a fileira move as capas horizontalmente;
nas bordas volta a rolar a página. Ctrl/Meta + roda preserva zoom. As coleções
também rolam horizontalmente, sem sobrepor nomes. O teclado virtual se adapta à
largura; o tema claro e a navegação por controle permanecem disponíveis.

Identidade compartilhada com Android: fundo `#0b1220`, texto `#edf4fd`, superfícies
`#1a2b3f`, destaque `#81e1ca` e seleção `#235e57`. Ficha/capas mostram selos
✓ Finalizado, ▶ Jogando, ★ nota e ⏱ tempo **deste PC**. 💾 indica save encontrado
na última consulta explícita a Saves durante esta sessão da página; abrir a
galeria não varre saves. Uma nova consulta sem save ou com erro retira o selo.
Não significa sincronização nem compatibilidade com o Android. Capas mantêm a
proporção sem cortar arte. O destaque abre **Ver jogo**, sem iniciar a partida.

**X** guarda/remove o jogo em foco nos favoritos; dentro da busca, continua apagando
uma letra. **Menu** abre opções: tema escuro/claro, tela cheia e volta ao início ou à
interface completa. O relógio usa o fuso do navegador e a bateria aparece quando
o navegador oferece essa informação. Favoritos e tema ficam em
`cache/tv_preferences.json`, com lock e gravação atômica, sem mudar a Biblioteca.
Recentes usam o histórico local de lançamentos; não exigem marcar o jogo como iniciado.
Continuar jogando usa iniciado sem finalizado, priorizando presença local e último uso.

O controle precisa chegar ao navegador como gamepad; o perfil Steam Input deve ser
conferido na instalação final para evitar ações duplicadas de mouse/teclado.

Biblioteca e Jogando oferecem filtros por plataforma. ROMs leves e pesadas oferecem
seleção por sistema. Cada capa abre os detalhes, priorizando **Jogar** quando disponível.
**Progresso e tempo** expande a edição de iniciado, finalizado, platinado e
nota entre 0 e 11, com ajustes de 1 ou 0,1. **Salvar progresso** aplica todas as
mudanças juntas; Voltar descarta alterações não salvas. A cascata mantém platinado
como finalizado e iniciado; desmarcar iniciado desmarca os dois seguintes.
O mesmo painel oferece **⏱ Registrar tempo**. A ação primária é **▶ Jogar neste PC**
(com nome da loja quando aplicável); Favoritar, Saves, Editar jogo, Capa e Texturas
usam os mesmos nomes do Android.

O catálogo pesado reaproveita o cache do Drive da GUI. Jogos só na nuvem aparecem
com **⬇ Baixar para este PC**, seguido de confirmação explícita. Durante o download é
possível voltar e navegar; o rodapé informa o resultado. O backend atual informa
início e resultado, sem percentual ou velocidade. Não recarregue a página durante
o download: o acompanhamento fica na sessão da página. Se a conexão cair, confira
a coleção antes de tentar novamente. O modo TV permite um download por vez na página;
outras abas e clientes continuam sujeitos às regras já existentes do backend.

## Sortear

A aba **🎲 Sortear** tem uma fileira de grupos (Tudo, ROMs leves/pesadas, Biblioteca e
seus subgrupos) e outra de gêneros. **Sortear** escolhe um jogo com o mesmo critério da
interface completa; o resultado abre os detalhes com foco em Jogar ou Transmitir,
quando disponível. O card permanece na grade ao voltar. ROM pesada só no Drive
oferece Baixar e jogar com confirmação. O sorteio apenas sugere; não inicia nada
automaticamente. Feche os detalhes e use o botão novamente para outro sorteio.

Na interface completa, o resultado também oferece Jogar (inclusive seleção de disco),
Transmitir do PS4/Xbox/Switch Lite ou abrir a loja quando o jogo não está instalado.
Baixar e jogar continua no modo TV, com o mesmo jogo aberto pelo link `?game=CHAVE`.
Falhas ficam visíveis e respostas antigas são ignoradas após sair do sorteio.
Jogos de Biblioteca são sorteados por ID; gênero/plataforma de homônimos não se misturam.

As sugestões remotas exigem a geração conhecida: PlayStation 4, Switch e Xbox
compatíveis com os clientes instalados. PS3, Xbox 360 e PSN sem geração definida
não são tratados automaticamente como PS4/Xbox One. Transmitir abre o cliente;
escolher o título no console continua sendo uma ação do usuário.

## Jogar e baixar sob demanda

Nos sistemas com lançador configurado, o card oferece **Jogar** quando há uma
ROM local completa. Quando há vários discos ou formatos, cada opção aparece
separadamente para você escolher, sem adivinhar qual abrir. Pastas de jogos são
examinadas para encontrar os arquivos executáveis pelo emulador. Jogos de PC
instalados na Steam, Epic, GOG ou Amazon (Heroic) mostram **Jogar (Steam/Heroic)**: o PyRetro pede à
loja já aberta que inicie o jogo, sem acompanhar a sessão, e o progresso é registrado
manualmente. Jogo não instalado avisa isso no card. A aba Jogando lista primeiro o que foi aberto
por último pela TV (data guardada em `cache/last_played.json`).

Para um jogo só no Drive, **Baixar e jogar** pede confirmação e abre o emulador
somente após o resultado positivo do download e uma nova validação dos arquivos.
Se o download contém vários discos/formatos, é preciso escolher qual abrir.
**Baixar para o PC** continua disponível sem iniciar nada. Descritores locais
incompletos podem oferecer **Completar download**, preservando os arquivos existentes.

CUE/GDI/M3U são conferidos junto com as referências. Não são aceitos arquivos
vazios, caminhos fora do sistema, ciclos de playlists ou symlinks externos.
CCD ainda não é liberado para jogar pela TV: falta validar IMG/SUB. Um sistema
sem mapeamento no lançador, como 3DS, continua disponível para progresso/download.

O download usa uma pasta temporária exclusiva no staging, fora de ROMs, e busca
as faixas referenciadas por descritores. Não reaproveita um arquivo antigo com o
mesmo nome no staging, não substitui arquivos locais e só publica depois que a
transferência termina. Pastas mantêm seu próprio diretório (o `rclone copy` copia
seu conteúdo). Staging e destino precisam estar no mesmo filesystem, como no
fluxo anterior por rename. A publicação de pastas sem sobrescrita usa renameat2
no Linux. Nunca há remoção de ROMs para liberar espaço.

O servidor acompanha uma sessão de emulador por vez. Ao sair, a TV oferece
registrar progresso e nota; não marca iniciado/finalizado automaticamente. Erros
de abertura ou saída são visíveis na TV; detalhes do processo vão para o journal
de `pyretro-gui`. Recarregar a página retoma o acompanhamento da sessão do servidor.
Ao terminar, o helper KWin tenta devolver o foco à janela PyRetro. A leitura do
controle fica suspensa com a janela em segundo plano ou o emulador em execução;
ao retornar, solte os botões antes de continuar. Foco real e captura pelo Steam Link
ainda precisam ser conferidos com os emuladores reais.

## Apps e emulador por jogo

Apps oferece os aplicativos de jogos instalados (Steam abre em Big Picture).
Início também oferece atalhos para Xbox remoto (Greenlight), PS4 remoto (Chiaki),
Steam, Heroic e os emuladores. Abrir o cliente usa sua autenticação/pareamento já
configurados; a integração não afirma que os consoles estão online ou pareados.
Xbox, PS4 e Switch reutilizam o cliente remoto já aberto, sem criar outra instância.
A conferência inclui processos Flatpak anteriores ao serviço e pedidos simultâneos;
a TV avisa para continuar na janela existente. Steam continua recebendo o pedido
de abrir Big Picture mesmo quando já está em execução.

Para abrir diretamente um PS4 já registrado, `cache/tv_remotes.json` aceita
`ps4_ip` (IP válido) e `ps4_nickname` (nome exato devolvido por `chiaki list`). O
cliente recebe `--fullscreen --exit-app-on-stream-exit stream NOME IP`, sem levar
chaves/tokens para o PyRetro. Sem esses campos, abre a interface normal do Chiaki.
Neste notebook foi encontrado PS4 registrado e preparado o acesso direto; a
descoberta no IP salvo não respondeu na conferência, então o teste da sessão
continua dependendo do console ligado/endereço atual. [Automação oficial do Chiaki](https://chiaki-ng.github.io/chiaki-ng/setup/automation/).
Entradas adicionais podem ser definidas como `[apps.identificador]`, com `nome`,
`icone` e `comando = ["executável", "argumento"]`. Só a configuração local fornece
comandos: a API recebe apenas o ID e revalida a lista a cada abertura, sem shell.

Nos cards de ROM, a escolha de emulador só aparece quando há uma alternativa
conhecida instalada. PicoDrive é oferecido para Mega Drive/Master System/Game Gear;
SwanStation para PS1, caso seu core exista. A escolha por jogo fica no perfil do
navegador, e arquivos/core são revalidados antes de abrir. O padrão continua usando
o lançador do setup.

### Switch Lite por Wi-Fi

O acesso **Switch Lite** aparece quando o cliente oficial SysDVR está instalado
(`com.github.exelix11.sysdvr`). O console precisa de SysDVR no Atmosphère e modo
**TCP Bridge** ativo no SysDVR Settings. O endereço pode ficar em
`cache/tv_remotes.json` como `{"switch_ip":"IP_DO_CONSOLE"}` (arquivo local ignorado
pelo Git). Apenas IP válido é aceito; sem endereço, usa descoberta automática.
O backend abre `bridge IP --fullscreen` com argumentos fixos, sem shell.

O SysDVR transmite áudio/vídeo dos jogos compatíveis; não captura o menu HOME e
não encaminha automaticamente o controle Xbox do PC. Use os controles do próprio
Switch para jogar. A versão padrão transmite 720p/30 fps; qualidade depende do
Wi-Fi. Consulte o [guia oficial](https://github.com/exelix11/SysDVR/wiki) e as
[limitações](https://github.com/exelix11/SysDVR#limitations).

Neste notebook o cliente 6.3 foi instalado da release oficial e o IP informado foi
guardado apenas no cache privado. A primeira conferência recusou as portas TCP
9911/9922; depois de ativar o console, Victor confirmou a transmissão funcionando
e foram verificadas as duas conexões ativas. Três players extras sem conexão foram
fechados, preservando a instância conectada. Nenhuma mudança foi feita pelo PyRetro
no Atmosphère ou no cartão SD.

## Xbox e atalhos dos emuladores

Perfil aplicado em 20/10/2026: Xbox Wireless Controller por Bluetooth, reconhecido
pelo SDL como Xbox One S Controller. `tools/configure_xbox.py` simula o plano;
`--apply` exige emuladores fechados e guarda cópias anteriores na auditoria privada.
Altera somente entrada/hotkeys e a confirmação de parada do Dolphin. Preserva
bindings de teclado do PCSX2/PPSSPP e opções gráficas/saves. Usa o perfil SDL oficial
do Dolphin para GameCube; Wii fica com Nunchuk no analógico esquerdo, ponteiro no
direito e sacudir no RB. Wii pode exigir ajuste específico de movimento/Classic Controller.

| Combinação Xbox | Ação |
|---|---|
| Back + LB | Salvar estado no slot selecionado |
| Back + RB | Carregar estado do slot selecionado |
| Back + ↑ / ↓ | Slot seguinte / anterior |
| Back + B | Pausar/retomar |
| Back + X | Captura de tela |
| Back + → | Acelerar (segurar no Dolphin; alternar nos demais) |
| Back + Start | Encerrar o jogo/emulador |
| Back + Y | Menu de pausa no RetroArch, PCSX2, DuckStation e PPSSPP |

Guide fica livre para o Bigscreen. O script não aciona save/load; a validação
inicial conferiu sintaxe oficial e acesso ao dispositivo nos quatro Flatpaks.
DuckStation é AppImage e acessa o dispositivo diretamente. Confirmação física
nos jogos e Steam Link continua com o usuário. Não foram criados/carregados estados
reais durante essa configuração.

## Atalho Steam e integração com setup-linux-bonesi

O script `tools/pyretro-tv.sh` inicia o serviço e abre o Chrome Flatpak em tela
cheia na URL local, com um perfil próprio dentro da configuração do Chrome.
Como o Big Picture fica ativo em tela cheia, o script chama `tools/raise-window.sh`
(KWin/Wayland via qdbus6) por até 25 s para trazer a janela do PyRetro para a frente;
sem isso ela abria atrás e não aparecia no Steam Link (achado em 16/10).
Isso mantém a janela independente do navegador de uso pessoal e mantém seu
processo ligado ao atalho até fechar a TV. O controle usa as permissões já
existentes do Chrome; não há relaxamento do sandbox do navegador.

Instalação: `python3 tools/install_tv.py` simula;
`python3 tools/install_tv.py --apply` instala com a Steam fechada. O instalador
adiciona **PyRetro**, preserva os atalhos existentes e guarda uma cópia
anterior do VDF em `~/.local/share/pyretro/steam-shortcuts/`. Havendo mais de uma
conta, exige `--config CAMINHO`. Não grava com a Steam aberta nem troca um atalho
que já exista com outro comando. Na máquina atual o atalho já foi instalado e renomeado de PyRetro — Acervo,
preservando appid e artes. O atalho web antigo fica oculto no menu; `/` continua acessível
pelo navegador. A entrada no Bigscreen é responsabilidade do botão Modo TV do setup,
sem alteração de boot/autostart pelo PyRetro.

A Steam Flatpak chama o script no host por `flatpak-spawn --host` (o mesmo padrão
que o ES-DE usava antes de sair do PC em 22/10/2026). O lançamento de ROMs pelo backend usa o
executável fixo `~/.local/bin/bonisarch-emulator`, sem shell nem comandos livres
recebidos do navegador. O mapeamento é explícito em `core/play.py`; o bridge
continua sendo mantido no setup-linux-bonesi. A pasta de ROMs configurada no
PyRetro precisa ser compatível com a pasta permitida por esse bridge.

## Validação

A suíte Python verifica rota/CSP, progresso em lote, preservação de outros campos
e recusa sem gravação parcial. A suíte `/tests/test_app.html` monta o modo TV
com APIs falsas, sem acessar dados reais, e verifica cascata, token CSRF,
restauração de foco, falha de gravação, confirmação de download, sucesso/falha SSE,
A/B simulados e largura de celular. Testes adicionais cobrem lançamento sem shell, sessão única, referências ausentes,
traversal/symlinks, download em staging, preservação de arquivos, pastas e atalhos
VDF. O ciclo baixar → abrir → encerrar também foi conferido em navegador com ROM
e lançador fictícios. Controle físico, Steam Input, download real e Steam Link
precisam de homologação na máquina.

A tela inicial também é testada com APIs falsas: atalhos remotos por ID, favoritos
sem repetição ao segurar X, falhas visíveis, persistência de tema, foco em Jogar e
ausência de escrita de progresso ao navegar/favoritar. A API verifica favoritos
concorrentes, rejeição de entradas inválidas e preservação integral da Biblioteca.

## Tempo jogado e mídia local

O servidor mede a duração do processo dos emuladores abertos por **Jogar**,
mesmo com a TV fechada, e registra uma única sessão ao encerrar. Esse intervalo
inclui pausas; não mede atividade no controle. Reiniciar/parar o servidor durante
uma sessão interrompe a medição. Steam, Heroic e clientes remotos podem manter
processos residentes: nesses casos use **Registrar tempo** nos detalhes, em minutos.
Isso não altera o campo histórico `tempo` da Biblioteca nem importa tempos das lojas.

Totais e sessões ficam em `cache/playtime.json`, com lock, escrita atômica e deduplicação
de eventos. A tela inicial oferece **Mais jogados** e os detalhes mostram o total.
Erro ao salvar tempo aparece sem deixar o emulador marcado como aberto.

**Personalizar mídia**, nos detalhes, aceita logo PNG/JPEG/WebP e prévia MP4/WebM,
até 64 MB por arquivo. As mídias ficam separadas em `cache/tv_media/`, por chave de
jogo; não substituem capas/ROMs do acervo. Imagens são validadas pelo ImageMagick e
vídeos pelo `ffprobe`. Arquivo inválido preserva a mídia anterior. Não faz busca
aproximada nem baixa trailers automaticamente. Vídeo em destaque é mudo e respeita
redução de movimento; nos detalhes pode ser reproduzido com controles. As URLs são
locais, com suporte a requisições Range, sem serviços de vídeo externos.
