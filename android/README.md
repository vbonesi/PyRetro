# PyRetro Android

App nativo em Kotlin, com Android 8 ou superior. O banco principal continua no
notebook; o APK não contém banco, contas, IPs, ROMs nem credenciais do Drive.

## Primeiro uso

1. Instale `PyRetro-0.7.0-debug.apk`. É uma compilação pessoal de teste, assinada
   com a chave local de debug; preserve essa chave para atualizar sem desinstalar.
2. Em **Opções → Configurar este celular**, escolha a **Pasta Jogos** (cada sistema
   fica em `Jogos/<sistema>`) e a **Pasta RetroArch** (saves e estados por sistema).
3. Salve o endereço HTTPS privado do PyRetro com **Salvar endereço e atualizar
   catálogo**, com o Tailscale conectado. O endereço não vem no APK.
4. **Neste celular** mostra arquivos locais; **Catálogo** também mostra os jogos
   que só estão no PC/Drive. A presença no notebook não conta como presença no
   celular. NDS/3DS têm prioridade de execução local.

## Hub de jogos (0.6)

O app é menos configurável à mão e mais direto. A estrutura é fixa: pastas
`Jogos/<sistema>`, saves e estados por sistema na pasta RetroArch, emuladores e
cores padrão (NES/Nestopia, PC Engine/Beetle PCE, NDS/melonDS, PS1/SwanStation…).
Mudanças nessa estrutura são feitas no próprio app, não em telas de opções.
Escolhas antigas de pasta por sistema e de core continuam respeitadas.

- **Início (0.6.2):** primeira coleção, com fileiras Continuar jogando, Recentes, Mais
  jogados, Favoritos e Prontos no celular, feitas só com dados do celular (funcionam
  offline). Recentes conta a partir da 0.6.2, quando o app passou a guardar a abertura.
- **Cabeçalho único:** Situação e Opções ficam só no topo, nas duas orientações;
  a barra abaixo tem as coleções (a ativa fica destacada) e **🎲 Sortear**.
- **Ficha do jogo:** a primeira ação é a que faz sentido para o jogo:
  **▶ Jogar neste celular**, **⬇ Baixar para este celular**, **📡 Transmitir do
  Xbox/PlayStation** (o jogo é escolhido no console; abrir direto não é possível),
  **📡 Transmitir do Switch pelo notebook** (SysDVR + Moonlight) ou **🖥 Jogar no
  notebook · Moonlight** para jogos de PC. Ao lado: favoritar, fixar e **💾 Saves**.
  Trocar ROM, texturas e remoção ficam em **Mais opções**.
- **Baixar em um toque:** com o notebook online, o celular pergunta ao PyRetro
  quais arquivos ele tem para o jogo (acervo do PC ou catálogo do Drive em cache)
  e baixa direto pelo Tailscale. ROMs que só estão no Drive vêm em streaming pelo
  `rclone` do notebook, sem gravar nada no PC. Há retomada por `Range`: a cópia
  parcial continua de onde parou, e a versão do arquivo (tamanho + data) é
  conferida em cada pedido; se a ROM mudou, o download para e pede descarte do
  parcial. Formatos que o celular não abre sozinho (CUE/BIN, M3U) não são
  oferecidos. Sem notebook, **Procurar a ROM no Drive** abre o seletor; escolher
  o arquivo já vincula ao jogo e inicia o download.
- **Atualiza sozinho:** quando o notebook responde, o catálogo é atualizado (se
  tiver mais de 6 h), o progresso e o tempo pendentes são enviados e as capas dos
  jogos do celular, favoritos e fixados vão para o cache offline. No máximo a cada
  15 min; conflitos continuam preservados para conferência. Saves não são
  automáticos: exigem os emuladores fechados e decisão nos conflitos.
- **💾 Saves deste jogo:** lista saves/estados do RetroArch do jogo (pasta do
  sistema, inclusive `ARCADE/fbneo/`) e, com o notebook, compara e sincroniza só
  esses arquivos, com escolha em conflitos e versões anteriores preservadas.
  PSP/3DS usam IDs próprios e abrem o grupo inteiro. Ao voltar de um jogo, o
  registro de tempo oferece **Salvar e ver saves**.

Sem notebook/Tailscale, continuam funcionando as pastas locais, catálogo já
carregado, últimas 128 capas consultadas, favoritos, progresso e tempo. O app
não importa `library.json` antigo do celular. Capas ficam no cache privado e
podem ser descartadas pelo Android; ROMs baixadas ficam na pasta compartilhada.

## Situação (0.6)

**Situação**, no topo, mostra uma linha por assunto e só oferece ação quando há
algo a fazer: jogos prontos no celular e data do catálogo, notebook online/offline
(com **Testar conexão**), progresso/tempo esperando envio, downloads, saves e
pastas. O restante fica recolhido em **Detalhes técnicos** (registro de contato,
cópias parciais, pastas e permissões, apps instalados). Abrir a tela não consulta
rede nem provedores.

### Central detalhada (histórico da 0.4)

A versão 0.4 reunia na central:

- Jogos da última leitura local, falhas de leitura e data do catálogo em cache;
  ações para abrir a coleção local, reler pastas e atualizar o catálogo.
- Último contato bem-sucedido e última tentativa com o notebook. **Testar conexão**
  faz uma consulta explícita ao PyRetro, sem sincronizar ou abrir jogos. Confira
  endereço HTTPS, notebook e Tailscale em caso de falha. O registro não garante
  conexão atual; trocar o endereço limpa os registros de contato anteriores.
- Progresso e sessões de tempo pendentes por jogo, com indicação dos itens que
  exigiram conferência na sincronização. Alterar a pendência invalida a indicação
  antiga; ela só reaparece se a nova versão for comparada e continuar bloqueada.
  Ações abrem os detalhes ou sincronizam explicitamente. Um jogo fora do catálogo
  permanece pendente; o app não cria seu cadastro automaticamente no notebook.
- Última análise/aplicação de cada grupo de saves, estados e runtime, com data,
  conflitos adiados e falhas. Mudar a pasta ou o endereço invalida a exibição do
  resultado correspondente. Analisar e aplicar continuam sendo ações distintas.
- Concessões de pastas não escolhidas, sem leitura persistente, somente leitura
  ou com leitura/escrita; tocar no item abre a escolha da pasta. São permissões
  salvas pelo Android, não uma prova de que a pasta/arquivo ainda existe. Pastas
  padrão de saves ausentes continuam sendo criadas só ao aplicar uma cópia.
- Vínculos da nuvem, número/tamanho dos checkpoints locais e atalhos para índice,
  downloads e playlists. **Emuladores, clientes e Tailscale** mostra os apps
  encontrados e permite abri-los; não verifica VPN, login, pareamento ou cores.

Abrir a central lê registros locais e permissões, sem consultar notebook/Drive
ou iniciar cópias. Dados anteriores à 0.4 podem aparecer sem data/resultado até a
próxima operação. A contagem local acompanha o fim da leitura inicial sem precisar
fechar a central, e o resumo de contato é atualizado após testar a conexão.
Pastas inválidas pedem nova escolha; observações de sincronização incompletas não
fecham a central. Diálogos com botões recebem foco na primeira ação disponível;
aplicativos ausentes ficam desativados na lista de conexões.

A 0.4 foi preparada sem celular. Após reconexão, a **0.4.1 foi instalada** no
usuário principal, com a assinatura preservada. Compilação, lint e 24 testes JVM
passaram; a instrumentação da central verificou retrato/paisagem, foco, concessões,
pendências e atualização dos resumos sem alterar progresso/tempo. A suíte de
armazenamento SAF também passou com fixtures próprias, e o inventário dos arquivos
reais permaneceu idêntico antes/depois. O teste explícito
com o notebook respondeu após reconectar o Tailscale já configurado. A pasta
RetroArch ainda precisa da concessão do usuário; G8 físico, Drive e sync real
continuam para homologação de uso.

## Controle e touch

Botões com alvo mínimo de 48 dp e grade de 2/3/4 colunas conforme a largura.
Galileo G8 e controles Android padrão: direcional/analógico move o foco, A abre,
B volta, X favorita, Y abre teclado virtual, LB/RB paginam (ou avançam a rolagem
quando não há outra página), LT/RT trocam coleção e Menu abre Opções. No teclado:
A digita, X apaga e Menu confirma. Touch usa também o teclado do Android.
Gatilhos por eixo são tratados. Controle conectado pede orientação horizontal
apenas no app; desconectar libera a orientação normal. O layout horizontal reduz
o cabeçalho e mantém capas proporcionais. Os mesmos comandos estão na tela para
touch. Não remapeia o controle dentro dos emuladores ou clientes de streaming.

**Sortear** respeita coleção, plataforma e gênero e abre os detalhes com as ações
disponíveis: jogar localmente, abrir o cliente remoto ou vincular/baixar a ROM.
Não inicia jogos, transmissões ou downloads automaticamente.

**Ranking** (0.8.0) lista só jogos com nota, a maior primeiro. **Filtro**, ao lado da
busca, escolhe plataforma e gênero entre os que existem na coleção aberta e zera ao
trocar de coleção. A ficha mostra a capa grande no topo, o tempo no celular e a nota;
o botão **Situação** ganha um número quando algo pede atenção (progresso esperando o
notebook, download com falha, pasta ilegível ou conflito de save).

**Desejados** (0.9.0) mostra as listas da Steam, PSN e Xbox (guardadas para ver offline), com
Comprado e Tirar da lista. **📊 Estatísticas** fica ao lado de Sortear. Na ficha, **Mais
opções** traz **✎ Editar dados** e **🖼 Trocar capa**; os três precisam do notebook online.

**Conta Google** (0.10.0, em Opções): com ela conectada, ROMs do seu Drive (`Jogos/ROMs`) baixam
sem o notebook. Os downloads continuam com o app em segundo plano, com notificação e Pausar.
Jogos em CUE/M3U baixam o conjunto inteiro pelo notebook; removê-los é pela pasta, por ora.

As barras de coleções e ações têm rolagem horizontal. A dica de controle some em
paisagem; a tela **Aparência** saiu na 0.6 (preferências antigas continuam
valendo). Erros operacionais continuam visíveis. Na ficha, **Progresso e tempo**
e **Mais opções** ficam recolhidos; a ação principal vem primeiro.

Para voltar de um jogo, use **Recentes do Android → PyRetro**. A coleção, busca,
página, rolagem e seleção são guardadas ao sair, inclusive para recriação do app.
Encerrar a partida depende do menu/atalho do emulador; o comportamento de Voltar
varia entre eles. O PyRetro não altera seus atalhos.

## Abrir jogos e transmissões

A aba **Stream**, na barra horizontal de coleções, reúne **Xbox · XBXPlay**,
**PS4 · Remote Play** e **PC e Switch · Moonlight**. Ela substitui a antiga fileira
de atalhos no topo. Busca e paginação de jogos ficam ocultas nessa aba; clientes
não instalados ficam desativados. Abrir a aba não liga consoles nem inicia sessões.
Para solicitar um título ao notebook, use a ação nos detalhes do jogo. Login,
pareamento e escolha do computador/console continuam nos clientes.

- RetroArch: intent explícito, ROM no armazenamento local, core padrão do PyRetro
  instalado no próprio RetroArch: NDS melonDS, PS1 SwanStation, NES Nestopia,
  PC Engine Beetle PCE. Desde a 0.6 não há escolha de core na interface; uma
  escolha feita antes continua valendo. Não baixa cores automaticamente.
- PPSSPP/PPSSPP Gold: `ACTION_VIEW` com URI e permissão de leitura.
- Lime3DS/Azahar: `ACTION_VIEW` com URI `content` e permissão de leitura.
- Xbox abre XBXPlay; PS4 abre o PS Remote Play oficial; PC abre Moonlight.
  Pareamento/login/seleção do console permanecem nesses aplicativos.
- Para jogos do notebook, a ação pede confirmação, solicita abertura ao servidor
  e abre Moonlight. Não há lançamento de NDS/3DS no PC por essa tela.

O app não instala cores, BIOS ou emuladores e não muda configurações existentes.
O lançamento precisa ser homologado no aparelho com os cores instalados. O
contrato do RetroArch usa caminho completo do core e a configuração padrão
externa; pode exigir ajuste conforme a instalação do usuário.

## ROM do Drive sob demanda

Na ficha do jogo, **Procurar a ROM no Drive** (ou **Mais opções → Escolher o
arquivo no Drive**) abre o seletor de arquivos do Android. Escolha o arquivo no
provedor Google Drive instalado e autenticado: ele fica vinculado ao jogo e o
download entra na fila e começa. A cópia usa o provedor e a pasta local escolhida,
sem passar pelo notebook/Tailscale. Precisa de internet para baixar;
concluído o download, funciona offline. Desde a 0.6 o caminho normal é **⬇ Baixar**
na ficha (veja Hub de jogos); o índice manual continua em **Opções → Avançado →
Índice manual do Drive**: escolha um sistema e adicione uma pasta
(se o provedor permitir) ou arquivos em lote. O app lê nomes/tamanhos e apresenta
uma prévia antes de guardar o índice. Correspondências únicas nos dois sentidos
são associadas ao catálogo; homônimos/edições ambíguas continuam separados para
escolha manual. ROMs sem registro no notebook aparecem como entradas da nuvem,
inclusive sem conexão ao PC. Vínculos manuais prevalecem sobre a atualização do
índice. **Atualizar índice** relê as origens concedidas; não há varredura de toda
a conta, OAuth embutido ou atualização periódica em segundo plano.

O seletor só mostra as operações oferecidas pelo provedor. Se o Drive não
permitir selecionar pastas, use **Adicionar arquivos em lote**. Limpar um índice
remove apenas seus metadados/vínculos automáticos; arquivos de origem e ROMs
locais permanecem. A indexação não baixa o conteúdo dos jogos.

**Opções → Downloads** permite controlar a fila e consultar/descartar cópias parciais.
Checkpoints persistem no armazenamento privado do app mesmo após encerrar o
processo. Ao continuar, URI/destino e metadados são conferidos; todo o prefixo
já baixado é comparado à origem antes de acrescentar bytes. Por isso o provedor
pode reler esse trecho: não há promessa de economia de tráfego nem suporte HTTP
Range pelo provedor. Origem diferente bloqueia a continuação até descartar o
checkpoint explicitamente. Depois de falha, escolha **Tentar novamente** no item
e inicie a fila; se a origem/pasta mudou, retire o registro e adicione-o novamente.

O app confere tamanho quando informado, SHA-256 e cópia final antes de publicar
na pasta local. Arquivo existente diferente nunca é substituído; uma cópia
idêntica pode ser reaproveitada. O limite é 12 GB por arquivo. A fase final usa
espaço para o checkpoint privado e a cópia na pasta local; reserve espaço para
ambos. A fila sequencial é iniciada pelo usuário; não há serviço de download em
segundo plano nem retomada automática ao abrir o app. Checkpoints antigos da 0.1
não são importados.

PS1 sob demanda aceita CHD/PBP. CUE/M3U com faixas/discos dependentes não são
baixados isoladamente. Os arquivos locais existentes nesses formatos podem ser
listados, mas o conjunto precisa estar completo no emulador. O app não converte
ROMs nem as envia ao Drive; remover a cópia local exige a confirmação descrita abaixo.

O acesso usa [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files):
o usuário escolhe os arquivos/pastas e o Android guarda as permissões concedidas.
Provedores podem exigir nova escolha se o arquivo for movido ou a permissão
expirar. Pastas privadas `Android/data` de outros apps não são acessíveis pelo
seletor em Android recente.

## Fila de downloads (0.5)

Em **Downloads**, inicie/continue, pause ou abra **Ver fila / reordenar itens**.
Cada jogo mostra estado e bytes; o tamanho total aparece quando o provedor o
informa. A fila processa um arquivo por vez, sem abrir o emulador ao concluir.
O andamento também aparece na tela principal. Você pode mover itens aguardando,
tentar novamente após falha e retirar registros concluídos. Há limite de 200
registros, incluindo concluídos. O mesmo documento para a mesma pasta não entra
duas vezes, mesmo com URIs SAF que representem a mesma identidade.

Ao sair do PyRetro a pausa é solicitada e o próximo item não começa. Uma publicação
final já conferida pode terminar durante a pausa. Falhas interrompem a sequência;
itens seguintes aguardam uma nova ação. Encerrar o processo preserva a fila e os
checkpoints; abrir novamente deixa downloads interrompidos pausados. **Retirar da
fila** mantém o parcial; **Descartar parcial** é uma ação separada. O app não apaga
ROMs automaticamente para abrir espaço. A origem e a pasta são guardadas no item
e conferidas antes de copiar; alterações exigem retirar/adicionar novamente.

## Espaço e jogos fixados (0.5)

Abra **Opções → Espaço e jogos fixados**. A leitura mostra ROMs locais por tamanho,
com filtros de sistema, finalizados, não finalizados, fixados e finalizados
removíveis. Tamanhos desconhecidos e falhas aparecem explicitamente. O total cobre
somente as ROMs encontradas nas pastas concedidas; saves, estados, BIOS, texturas
e versões anteriores ficam fora desse total. Downloads informa checkpoints; o
espaço livre apresentado é o disponível ao app/checkpoints, sem prometer a mesma
capacidade em qualquer destino SAF.

**Fixar ROM**, nos detalhes ou no gerenciador, significa manter baixado; é separado
de favorito e pode ser escolhido antes do download. A proteção acompanha a ROM
baixada e vale para aliases do mesmo documento. Para remover, desfixe primeiro.
Não há remoção automática ao finalizar um jogo fixado.

A remoção é individual e exige confirmação. Itens na fila e descritores CUE/M3U
ficam protegidos. Nome, tamanho e data do arquivo são conferidos novamente antes
de apagar; mudanças desde a leitura bloqueiam a operação. Saves, estados,
texturas, histórico, progresso e origem continuam preservados. Nenhuma política
de retenção de versões ou limpeza em lote foi ativada.

## Progresso, tempo e arquivos existentes

Progresso é guardado localmente, com a mesma cascata iniciado/finalizado/platinado.
Desde a 0.6 o envio é automático quando o notebook responde (ou **Enviar agora**
em Situação): compara o estado visto na edição com o atual, revalida sob lock no
servidor e preserva conflitos. Identidade
é a chave do catálogo; jogos locais sem vínculo com o banco não criam cadastros.

Ao voltar de um emulador aberto pelo app, ele propõe os minutos decorridos. O
usuário confirma ou descarta, pois esse intervalo pode incluir pausas/outros apps.
Eventos têm identificador para que uma repetição da sincronização não duplique
a sessão no servidor. Não lê nem soma automaticamente runtime logs antigos.

Desde a versão 0.2, **Opções → Saves e estados · todos os jogos** oferece sincronização
por grupos: saves/estados/runtime do RetroArch, SAVEDATA/PPSSPP_STATE do PPSSPP e
saves/extdata do SDMC do 3DS. O notebook usa os diretórios de saves configurados;
PPSSPP fica em `Saves/PPSSPP/` e 3DS em `Saves/Lime3DS/sdmc/`.

1. Escolha **Pasta RetroArch** uma vez. Saves e estados usam `saves/` e `states/`;
   runtime usa `playlists/logs/`, conforme o padrão encontrado no aparelho. Se
   mudou esses caminhos no emulador, escolha a pasta de cada grupo separadamente.
   PSP/3DS aproveitam a pasta Jogos já concedida, com opção de trocar o destino.
   Uma subpasta padrão ainda inexistente fica vazia na análise; só é criada ao
   aplicar a primeira cópia para ela.
2. Feche os emuladores nas duas pontas e use **Analisar sem copiar**. O app compara
   SHA-256 com o último estado comum; a análise não altera arquivos.
3. Arquivos diferentes na primeira sincronização ou alterados nos dois lados são
   conflitos. Escolha celular, notebook ou adiar individualmente. Ausência de um
   arquivo já sincronizado também exige decisão; não propaga exclusões.
4. **Aplicar escolhas** confirma o plano. Origem/destino e checksum são conferidos
   novamente. Transferência incompleta não substitui o save; falhas ficam no resultado.

No PC, versões anteriores ficam em `.pyretro-history/<caminho original>/` na
pasta do grupo. No celular, ficam ao lado do save com prefixo
`.pyretro-previous-`. Desde a versão 0.3, abra o grupo e escolha
**Versões deste celular** (offline)
ou **Versões do notebook** (conectado), selecione uma versão e confirme restaurar.
No segundo caso a restauração acontece no PC; analise o grupo para recebê-la no
telefone. O arquivo atual e a versão escolhida ficam preservados. Alteração do
destino desde a listagem bloqueia a operação; abra novamente o histórico.
Também é possível recuperar pelo gerenciador com arquivos ocultos visíveis.
Não são apagadas automaticamente. Históricos não entram na próxima sincronização.

Estados precisam de core/versão compatíveis. Runtime é copiado como arquivo, sem
somar tempos acumulados nem importá-los automaticamente no tempo do PyRetro.
3DS inclui somente `title/.../data` e `extdata`; não copia jogos instalados,
NAND, firmware ou configurações. BIOS/texturas/configurações não fazem parte desses
planos. A restauração não redefine automaticamente o último estado comum de
sincronização; analise o grupo antes de enviar a versão restaurada à outra ponta.
Não use FolderSync em paralelo nas mesmas pastas.

Ao marcar um jogo baixado como **Finalizado** (inclusive pela cascata de
Platinado), o app pergunta **Manter ROM** ou **Excluir ROM local**, salvo se o
jogo estiver fixado para manter baixado. A remoção
também está nos detalhes e só alcança o arquivo de ROM na pasta local escolhida.
Progresso, favorito, tempo, saves, states, BIOS, capas, texturas e a origem no
PC/Drive ficam preservados. CUE/M3U exigem conferir faixas/discos no gerenciador
do notebook; o app recusa apagar um descritor isolado. As playlists externas
do RetroArch só são modificadas se você habilitar a função abaixo. Não há limpeza
automática em lote.

## Playlists do RetroArch

Desde a versão 0.3, **Opções → Avançado → Playlists do RetroArch** gera/atualiza a playlist
JSON convencional de cada sistema compatível, usando apenas ROMs presentes no
telefone. A concessão da pasta RetroArch é a mesma usada pelos saves; o destino
é `playlists/<nome do sistema>.lpl`. PSP/3DS ficam nos emuladores próprios.

Use **Analisar atualização** para ver quantas entradas serão adicionadas/removidas.
Só são retiradas entradas ausentes da raiz local e das extensões do sistema
escolhido; itens de outras pastas e campos existentes (rótulos, core, CRC etc.)
permanecem. Novas entradas usam `DETECT`, no formato documentado pelo
[RetroArch](https://docs.libretro.com/guides/roms-playlists-thumbnails/).
Playlists antigas não JSON são preservadas e exigem conversão pelo RetroArch.
Falha de permissão, lista incompleta ou mudança de arquivos aborta a atualização.

Feche o RetroArch antes de aplicar. A versão anterior fica no histórico e pode
ser restaurada pelo submenu **Recuperar versão anterior**. Uma restauração
suspende a atualização automática até nova análise. A opção de atualizar após
download/remoção de ROM pelo PyRetro é voluntária; pode ser desativada por sistema.
Mudança de pastas exige nova ativação. Operações externas exigem análise manual;
o APK não monitora os emuladores. CUE/M3U locais entram como descritores: sua
presença não comprova que todas as faixas/discos existem.

## Texturas PSP e 3DS

**Texturas** oferece fontes PSP já verificadas pelo notebook e upload de ZIP,
7z ou RAR local. Confira o ID/região: PSP usa quatro letras e cinco números;
3DS usa title ID de 16 hexadecimais. Feche o emulador antes de instalar.

- ZIP local funciona offline. RAR/7z é enviado ao notebook para preparação;
  catálogo PSP também é baixado/verificado nele e recebido como ZIP pelo celular.
- Destinos relativos à pasta escolhida: PSP `PSP/TEXTURES/<ID>`; 3DS
  `load/textures/<ID>`. Ative carregar/substituir texturas no emulador.
- Caminhos fora da pasta e pacotes acima de 12 GB/50 mil arquivos são recusados.
  Arquivos idênticos são reaproveitados; uma textura diferente existente bloqueia
  a instalação antes de substituir arquivos.
- PS1/DuckStation exige o gerenciador do notebook via USB por causa das restrições
  de `Android/data`; fontes locais também podem ser enviadas pela interface web.

## Compilar e verificar

Requer JDK 17, SDK Platform 35, Build Tools 35.0.0 e platform-tools (toolchain
local em `~/.cache/pyretro/android-toolchain/{jdk,sdk}`). Com
`JAVA_HOME` e `ANDROID_HOME` configurados, na raiz do repositório:

```bash
python3 tools/build_android.py
```

O wrapper usa Gradle 8.13, AGP 8.13.0 e Kotlin 2.1.20. Na primeira execução o
Gradle baixa a distribuição/dependências oficiais. Para usar Gradle já instalado,
adicione `--gradle /caminho/gradle`. O script cria a chave local de debug em
`android/.gradle/debug.keystore`, executa build, testes JVM e lint, e copia APK e
SHA-256 para `cache/artifacts/`, ignorados pelo Git. Não publicar a chave.

Instalação posterior, com depuração USB autorizada:

```bash
adb install --user 0 -r cache/artifacts/PyRetro-0.7.0-debug.apk
```

A **0.7.0 (code 13) está instalada** desde 22/10/2026 (43 testes JVM, build e lint).
A 0.6 foi validada no aparelho nesse dia: download do PC e do Drive com pausa e
retomada, saves por jogo online/offline, stream e Situação/Opções nas duas
orientações. A suíte de status desliga a atualização automática durante a navegação
de consulta; ela ainda não rodou no aparelho com a 0.6/0.7.

Histórico: a versão **0.5.1** foi instalada no usuário principal com a mesma assinatura.
Compilação/lint e 29 testes JVM aprovados. A instrumentação de interface verifica
retrato/paisagem, central, menus de espaço/downloads, aba Stream e restauração de
coleção/página após recriação. A suíte SAF usa arquivos próprios para conferir
fila, interrupção/retomada, reordenação, deduplicação, fixação por alias e recusa
de remoção se o arquivo mudar. Nenhum jogo ou save real é usado nessas operações.

Compilação, lint e 24 testes JVM passaram para a versão 0.4.1, instalada no
usuário principal após reconexão. A central foi exercitada no aparelho em retrato
e paisagem, com foco e preferências de teste isoladas. A suíte de armazenamento
SAF foi reexecutada com sucesso. A versão 0.3 passou em 18 testes JVM e foi instalada
no usuário principal do aparelho. A instrumentação da 0.3 passou
com arquivos sintéticos: recuperação de versões, índice em lote, download pausado/
retomado e playlists preservando campos/itens externos. Inventário real de ROMs,
saves, estados e playlists conferido igual antes/depois; fixtures removidas.
Nas versões anteriores já foram conferidos catálogo via HTTPS/Tailscale, cache
offline, pastas existentes, sorteio, ZIP mínimo, remoção e NES/Nestopia. Instalação limitada ao perfil principal evita
cópias no perfil Dual App da Samsung; novas aberturas reutilizam a mesma tela.
Galileo G8 físico e download real pelo provedor Google Drive ainda precisam de
homologação; eventos de botões padrão são apenas uma verificação de software.

Contrato de lançamento: [documentação oficial do RetroArch](https://docs.libretro.com/guides/cli-intro/#on-android).
Core ausente pode deixar a atividade externa na tela preta: [issue 19357](https://github.com/libretro/RetroArch/issues/19357).
O APK não pode inspecionar a pasta privada de cores de outro app; escolha um core instalado.

Teste técnico de armazenamento no aparelho (usa somente pasta sintética própria):
`./gradlew :app:assembleDebugAndroidTest`, instale o APK de teste no usuário 0 e
execute `adb shell am instrument -w com.pyretro.app.test/com.pyretro.app.StorageSmoke`.
O teste exige a concessão Pasta Jogos e remove seus arquivos ao terminar.
Na versão 0.3 ele também cobre restauração, índice em lote, download interrompido/
retomado e preservação dos campos de playlists, com preferências e pasta sintéticas
isoladas. Foi executado com sucesso no aparelho reconectado. O teste exige que a
raiz derivada permaneça dentro da pasta sintética antes de iniciar as cópias.
Na 0.5, cobre também fila persistente, pausa/retomada/reordenação, deduplicação,
espaço, fixação e revalidação de remoção. Não homologa o provedor Google Drive.
Desinstale somente `com.pyretro.app.test` depois da execução; o aplicativo principal
e suas permissões permanecem instalados.

Suíte da central (preferências isoladas, sem copiar saves ou abrir jogos):
`adb shell am instrument -w -e suite status com.pyretro.app.test/com.pyretro.app.StorageSmoke`.
Ela verifica também pastas inválidas, observações incompletas, foco inicial,
leitura local concluída com a central aberta e ausência de alterações nas
preferências reais. Para testar explicitamente a consulta ao notebook e o resumo
atualizado na mesma tela, adicione `-e connection true`; só os registros de contato
reais podem mudar. As duas orientações são verificadas na configuração efetiva do
app. Desbloqueie o aparelho para a execução.
