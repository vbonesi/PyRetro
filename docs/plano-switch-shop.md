# Plano: "PyRetro Shop" para o Switch (11/11/2026)

Só planejado; nada implementado.

## Objetivo

Instalar no Switch (Atmosphère) os dumps de Switch do próprio acervo, que estão na pasta
`NSW` do Drive, **de qualquer rede**, sem o PC ligado. A emulação e o catálogo continuam no
celular: o Switch só recebe os jogos dele.

## Decisões

- O PyRetro **não** vira app de Switch. O PC gera um índice no formato de "shop" do
  Tinfoil, e o Switch lê os arquivos direto do Drive por OAuth (`gdrive:/<ID do arquivo>`).
- O cliente no Switch é o **Tinfoil**: entre as opções pesquisadas, é o único com leitura do
  Google Drive autenticada documentada. CyberFoil e Sphaira ficam como alternativa se um dia
  lerem o Drive.
- A pasta não fica pública: OAuth com cliente próprio do Switch e escopo somente leitura,
  revogável se o console sumir.
- O índice traz nomes e IDs do acervo e por isso **fica só no Drive**, nunca no repositório
  (mesma regra do mapa do NSW).

## Base existente

- Os arquivos em `NSW/<Jogo>/` já trazem `[TitleID][vVersão]` no nome (base `…000`, update
  `…800`, DLC o resto). Isso é o que o Tinfoil usa para identificar o jogo e buscar a capa.
- `rclone lsjson` devolve o `ID` de cada arquivo no Drive (`core/heavy_roms.py`,
  `list_drive_items`). `core/switch_upload.py` define as extensões (`.nsp .nsz .xci .xcz`)
  e é o caminho de entrada dos dumps.

## Itens

**V1. Teste à mão no Switch (Victor). Pronto quando:** o Tinfoil com `credentials.json` e
token no SD lista a pasta `gdrive:/<ID da pasta NSW>` e instala um jogo pequeno fora da rede
de casa (por exemplo, roteado do celular). Anotar se o Tinfoil aceita um índice `.json`
lido pelo `gdrive:/` e que escopo o token pede.

**P1. Gerador do índice (`core/switch_shop.py`). Pronto quando:**
- uma única chamada `rclone lsjson -R` na pasta `NSW` gera o JSON do Tinfoil, com
  `files: [{"url": "gdrive:/<ID>#<nome do arquivo>", "size": N}]` e uma mensagem `success`
  com a data e a contagem;
- ficam de fora arquivos parciais (`.part`, `.crdownload` etc.) e as extensões não
  suportadas;
- o índice sobe para `PyRetro-Nuvem/switch/` no Drive com `rclone rcat`/`copyto`, com a
  versão anterior substituída;
- é chamado pela CLI, por um botão "Atualizar índice do Switch" em 🛠 Ferramentas no modo TV
  e ao fim de `switch_upload` quando um jogo novo sobe;
- os testes usam `lsjson` falso (nomes, IDs, parciais, pasta vazia, falha do rclone sem
  gravar nada) e passam junto com a suíte inteira;
- nenhum nome ou ID real entra no Git.

**P2. Credencial do Tinfoil pelo PyRetro (11/11). Pronto quando:** um comando do PyRetro
faz o login OAuth no navegador do PC (fluxo de app instalado, retorno em `127.0.0.1`, só
biblioteca padrão) com o `credentials.json` do cliente Desktop "Switch" e grava
`credentials.json` + `gdrive.token` no formato que o Tinfoil lê, numa pasta fora do
repositório pronta para copiar em `/switch/tinfoil/` do SD. Arquivos com permissão 0600; o
token nunca aparece na saída nem nos logs. Escopo `drive.readonly` primeiro; se o Tinfoil
recusar, o comando aceita escolher `drive`. Testes cobrem o formato gerado e a troca de
código com o Google simulada. Substitui o uso do rustfoil.

**V2. Uso real (Victor). Pronto quando:** o Tinfoil aponta para o índice no Drive, mostra
os jogos com nome e capa e instala um remotamente.

**L1. Documentação.** README (seção curta de uso), `docs/changelog.md` e `docs/roadmap.md`.

## Riscos e dúvidas

- O Tinfoil é de código fechado e exige o DNS MITM do Exosphère. Se mudar de comportamento,
  o índice continua servindo para outro cliente compatível.
- Pode ser que o Tinfoil exija escopo de Drive inteiro em vez de somente leitura (ver no V1).
- Cota de download do Google: com OAuth próprio não há a cota dos links públicos, mas
  downloads grandes seguidos podem sofrer limite temporário.
- O SD precisa estar em exFAT (há jogos com mais de 4 GB).
- NPShop (homebrew de saves que o Victor usa) só enxerga a pasta que ele mesmo cria: não
  substitui o Tinfoil.

## Andamento

- 11/11/2026: P1, P2 e L1 feitos. **V1 feito em casa:** fonte cadastrada pelo botão "−" do
  File Browser (Protocol `gdrive`, demais campos vazios); um jogo pequeno instalou do Drive e
  rodou. O primeiro acesso a uma pasta de jogo deu "Failed query gdrive access token";
  reiniciar o Tinfoil resolveu. Faltam o teste fora de casa e o V2 (índice).
