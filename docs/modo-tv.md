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
O controle precisa chegar ao navegador como gamepad; o perfil Steam Input deve ser
conferido na instalação final para evitar ações duplicadas de mouse/teclado.

Biblioteca e Jogando oferecem filtros por plataforma. ROMs leves e pesadas oferecem
seleção por sistema. Cada capa abre o progresso: iniciado, finalizado, platinado e
nota entre 0 e 11, com ajustes de 1 ou 0,1. **Salvar progresso** aplica todas as
mudanças juntas; Voltar descarta alterações não salvas. A cascata mantém platinado
como finalizado e iniciado; desmarcar iniciado desmarca os dois seguintes.

O catálogo pesado reaproveita o cache do Drive da GUI. Jogos só na nuvem aparecem
com **Baixar para o PC**, seguido de confirmação explícita. Durante o download é
possível voltar e navegar; o rodapé informa o resultado. O backend atual informa
início e resultado, sem percentual ou velocidade. Não recarregue a página durante
o download: o acompanhamento fica na sessão da página. Se a conexão cair, confira
a coleção antes de tentar novamente. O modo TV permite um download por vez na página;
outras abas e clientes continuam sujeitos às regras já existentes do backend.

## Sortear

A aba **🎲 Sortear** tem uma fileira de grupos (Tudo, ROMs leves/pesadas, Biblioteca e
seus subgrupos) e outra de gêneros. **Sortear** escolhe um jogo com o mesmo critério da
interface completa; o resultado aparece como card, com Jogar/Baixar/progresso. ROM pesada
sorteada pode estar só no Drive: o card oferece Baixar e jogar. Use o botão de novo
para outro sorteio.

## Jogar e baixar sob demanda

Nos sistemas com lançador configurado, o card oferece **Jogar** quando há uma
ROM local completa. Quando há vários discos ou formatos, cada opção aparece
separadamente para você escolher, sem adivinhar qual abrir. Pastas de jogos são
examinadas para encontrar os arquivos executáveis pelo emulador. Jogos de PC
instalados na Steam, Epic ou GOG (Heroic) mostram **Jogar (Steam/Heroic)**: o PyRetro pede à
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
O retorno do foco da janela e a captura pelo Steam Link dependem da sessão gráfica
e precisam ser conferidos com os emuladores reais.

## Atalho Steam e integração com setup-linux-bonesi

O script `tools/pyretro-tv.sh` inicia o serviço e abre o Chrome Flatpak em tela
cheia na URL local, com um perfil próprio dentro da configuração do Chrome.
Isso mantém a janela independente do navegador de uso pessoal e mantém seu
processo ligado ao atalho até fechar a TV. O controle usa as permissões já
existentes do Chrome; não há relaxamento do sandbox do navegador.

Instalação: `python3 tools/install_tv.py` simula;
`python3 tools/install_tv.py --apply` instala com a Steam fechada. O instalador
adiciona **PyRetro — Acervo**, preserva os atalhos existentes e guarda uma cópia
anterior do VDF em `~/.local/share/pyretro/steam-shortcuts/`. Havendo mais de uma
conta, exige `--config CAMINHO`. Não grava com a Steam aberta nem troca um atalho
que já exista com outro comando. Na máquina atual o atalho já foi instalado.

A Steam Flatpak chama o script no host por `flatpak-spawn --host`, seguindo o
padrão do ES-DE instalado pelo setup. O lançamento de ROMs pelo backend usa o
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
