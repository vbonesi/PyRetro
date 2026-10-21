# PyRetro Android

App nativo em Kotlin, com Android 8 ou superior. O banco principal continua no
notebook; o APK não contém banco, contas, IPs, ROMs nem credenciais do Drive.

## Primeiro uso

1. Instale `PyRetro-0.2.0-debug.apk`. É uma compilação pessoal de teste, assinada
   com a chave local de debug; preserve essa chave para atualizar sem desinstalar.
2. Em **Opções**, escolha **Pasta Jogos · reconhecer todos os sistemas**, ou cada
   pasta separadamente. Arquivos que eram sincronizados pelo FolderSync são reaproveitados.
3. Opcionalmente salve o endereço HTTPS privado do PyRetro e escolha **Carregar
   catálogo do notebook**, com o Tailscale conectado. O endereço não vem no APK.
4. **Neste celular** mostra arquivos locais; **Catálogo em cache** também mostra
   os jogos que só estão no PC/nuvem. A presença no notebook não conta como
   presença no celular. NDS/3DS têm prioridade de execução local.

Sem notebook/Tailscale, continuam funcionando as pastas locais, catálogo já
carregado, últimas 128 capas consultadas, favoritos, progresso e tempo. O app
não importa `library.json` antigo do celular. Capas ficam no cache privado e
podem ser descartadas pelo Android; ROMs baixadas ficam na pasta compartilhada.

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

## Abrir jogos e transmissões

- RetroArch: intent explícito, ROM no armazenamento local, core instalado no
  próprio RetroArch; NDS oferece melonDS (padrão), melonDS DS ou DeSmuME. PS1 usa SwanStation.
  **Cores do RetroArch por sistema**, em Opções (ou nos detalhes do jogo), permite
  escolher um core já instalado. NES usa Nestopia e PC Engine usa Beetle PCE
  por padrão, conforme a instalação conferida; não baixa cores automaticamente.
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

Nos detalhes de um jogo, **Vincular ROM no Drive** abre o seletor de arquivos do
Android. Escolha o arquivo no provedor Google Drive instalado e autenticado.
Depois, **Baixar ROM vinculada e jogar** copia pelo provedor para a pasta local
escolhida, sem passar pelo notebook/Tailscale. Precisa de internet para baixar;
concluído o download, funciona offline. A associação é escolhida uma vez por
jogo; não há indexação automática de todo o Drive nem OAuth embutido no APK.

A cópia usa `.part` exclusivo, confere o tamanho quando informado pelo provedor
e só publica o nome final após concluir. Arquivo existente nunca é substituído.
Um download interrompido pelo encerramento forçado do app pode deixar um `.part`
sem entrar na biblioteca; não há retomada automática nesta versão.

PS1 sob demanda aceita CHD/PBP. CUE/M3U com faixas/discos dependentes não são
baixados isoladamente. Os arquivos locais existentes nesses formatos podem ser
listados, mas o conjunto precisa estar completo no emulador. O app não converte
ROMs nem as envia ao Drive; remover a cópia local exige a confirmação descrita abaixo.

O acesso usa [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files):
o usuário escolhe os arquivos/pastas e o Android guarda as permissões concedidas.
Provedores podem exigir nova escolha se o arquivo for movido ou a permissão
expirar. Pastas privadas `Android/data` de outros apps não são acessíveis pelo
seletor em Android recente.

## Progresso, tempo e arquivos existentes

Progresso é guardado localmente, com a mesma cascata iniciado/finalizado/platinado.
**Sincronizar progresso e tempo** é explícito: compara o estado visto na edição
com o estado atual, revalida sob lock no servidor e preserva conflitos. Identidade
é a chave do catálogo; jogos locais sem vínculo com o banco não criam cadastros.

Ao voltar de um emulador aberto pelo app, ele propõe os minutos decorridos. O
usuário confirma ou descarta, pois esse intervalo pode incluir pausas/outros apps.
Eventos têm identificador para que uma repetição da sincronização não duplique
a sessão no servidor. Não lê nem soma automaticamente runtime logs antigos.

Desde a versão 0.2, **Opções → Saves, estados e runtime** oferece sincronização
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
`.pyretro-previous-`. Ative mostrar arquivos ocultos no gerenciador para recuperá-las.
Não são apagadas automaticamente. Históricos não entram na próxima sincronização.

Estados precisam de core/versão compatíveis. Runtime é copiado como arquivo, sem
somar tempos acumulados nem importá-los automaticamente no tempo do PyRetro.
3DS inclui somente `title/.../data` e `extdata`; não copia jogos instalados,
NAND, firmware ou configurações. BIOS/texturas/configurações não fazem parte desses
planos. Playlists externas e retomada de downloads continuam nas próximas etapas.
Não use FolderSync em paralelo nas mesmas pastas.

Ao marcar um jogo baixado como **Finalizado** (inclusive pela cascata de
Platinado), o app pergunta **Manter ROM** ou **Excluir ROM local**. A remoção
também está nos detalhes e só alcança o arquivo de ROM na pasta local escolhida.
Progresso, favorito, tempo, saves, states, BIOS, capas, texturas e a origem no
PC/Drive ficam preservados. CUE/M3U exigem conferir faixas/discos no gerenciador
do notebook; o app recusa apagar um descritor isolado. As playlists externas
do RetroArch não são modificadas pelo APK. Não há limpeza automática em lote.

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

Requer JDK 17, SDK Platform 35, Build Tools 35.0.0 e platform-tools. Com
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
adb install --user 0 -r cache/artifacts/PyRetro-0.2.0-debug.apk
```

Compilação, lint e dez testes JVM passaram. APK instalado no aparelho:
catálogo via HTTPS/Tailscale, cache offline, pastas existentes, sorteio, ZIP
de textura mínimo, confirmação de remoção e lançamento NES/Nestopia conferidos. Instalação limitada ao perfil principal evita
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
Desinstale somente `com.pyretro.app.test` depois da execução; o aplicativo principal
e suas permissões permanecem instalados.
