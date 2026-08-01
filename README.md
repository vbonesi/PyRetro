# PyRetro

CLI de manutenção do meu acervo de RetroArch (PC + Android), pra manter as
duas plataformas o mais parecidas possível sem precisar fazer tudo na mão.

Escopo intencional: o script só mexe em duas coisas — a pasta sincronizada
(`~/Drive/Jogos`, via Insync/Google Drive) e o celular Android via `adb`.
Ele nunca precisa que RetroArch, DuckStation, PCSX2 etc. estejam instalados
na máquina onde ele roda, porque todos esses emuladores já foram configurados
pra ler/escrever direto na pasta sincronizada. Isso é proposital: dá pra
rodar o PyRetro de qualquer computador que tenha acesso à pasta e ao celular,
sem precisar reinstalar nada específico de emulador ali.

## Princípios (não mudar sem revisitar o motivo)

Essas regras existem por causa de incidentes reais durante o desenvolvimento,
não são só estilo:

- **Nunca apaga nada sozinho.** Toda operação é aditiva (copia o que falta,
  atualiza o que mudou). Remoção é sempre uma decisão manual, fora do script.
- **Nunca transfere jogo novo.** O script corrige/organiza o que já existe
  no acervo, não decide baixar ou copiar ROM pra lugar nenhum.
- **Fuzzy match nunca é aplicado sozinho.** Correspondência aproximada de
  nome (capas, principalmente) só entra num relatório pra revisão humana -
  mesmo com corte de similaridade alto (90%+), sequências como "Dragon Quest"
  vs "Dragon Quest II" já geraram capa errada aplicada sem querer.
- **Tudo roda em modo simulação por padrão.** Todo comando só escreve/copia
  de verdade com `--apply` explícito.
- **`.cue` sem `.bin` não é lixo.** É uma ROM que ainda vai ser baixada sob
  demanda (o acervo de PS1 é maior que o espaço que vale a pena manter
  local o tempo todo). Nunca deletar `.cue` órfão.
- **Capa sem ROM correspondente não é lixo.** O acervo de capas é
  intencionalmente maior que o de ROMs, pelo mesmo motivo acima.

## Requisitos

- Python 3.11+ (usa `tomllib` da stdlib, sem dependência externa)
- `adb` no PATH, com o celular autorizado (`adb devices` deve listar o
  aparelho como `device`, não `unauthorized`/`offline`)
- `curl` no PATH (usado pro download de capas)

Sem `pip install` nenhum - tudo é stdlib de propósito, pra rodar em qualquer
máquina sem setup de ambiente virtual.

## Setup

```bash
cp config.example.toml config.toml
```

Edite `config.toml`: a seção `[pc]` tem os caminhos da pasta sincronizada
(`roms_root`, `capas_root`, `saves_root`...), a `[android]` os caminhos
equivalentes no celular. As seções `[systems.*]` mapeiam cada pasta de
sistema pro repositório de capas certo em `github.com/libretro-thumbnails/`
- normalmente não precisa mexer nelas.

`config.toml` está no `.gitignore` (é específico da sua máquina/celular).

## Comandos

### `fetch-covers` — busca capas no libretro-thumbnails

```bash
python3 retrosync.py fetch-covers PS              # simula, mostra o que faria
python3 retrosync.py fetch-covers PS --apply       # baixa de verdade
python3 retrosync.py fetch-covers all --apply      # todos os sistemas do config.toml
```

Casamento de nome em duas etapas: exato (normalizando tags de região/rev/beta)
e, se não achar, aproximado - mas aproximado só entra no relatório final,
nunca é baixado sozinho. Pra sistemas como Arcade, onde o nome do arquivo é
um código curto de ROM (`dariusg`, `karnovr`...), o script primeiro resolve
o nome de verdade via o `.dat` oficial do FBNeo antes de tentar casar contra
o repositório de capas - resolve a maioria dos casos que fuzzy match sozinho
erraria.

### `fetch-covers-fallback` — segunda fonte pros que sobraram (LaunchBox Games DB)

```bash
python3 retrosync.py fetch-covers-fallback SFC              # simula
python3 retrosync.py fetch-covers-fallback all --apply       # baixa de verdade
```

Só olha os itens que o `fetch-covers` já marcou como `sem_match` no
registro - não reprocessa tudo. Usa o [LaunchBox Games
Database](https://gamesdb.launchbox-app.com/) (não precisa de conta/API
key - baixa o `Metadata.zip` público deles, ~500MB descompactado, faz um
índice filtrado e cacheia em `cache/launchbox_index.json`; só reprocessa o
XML de novo com `--rebuild-index`). Tem cobertura melhor pra hack/tradução
de fã que o libretro-thumbnails não cataloga.

Casamento exato primeiro; se não achar, tenta por PREFIXO de palavras (o
arquivo local geralmente não tem o subtítulo que o LaunchBox guarda por
extenso, ex: local "Zool" vs LaunchBox "Zool: Ninja of the 'Nth'
Dimension") - com trava de segurança pra não deixar "Contra" casar com
"Contra III" (a palavra logo após o prefixo não pode ser um número/numeral
romano sozinho).

### `sync` — sincroniza saves/states/métricas/capas PC ↔ Android

**Ainda não implementado** (`core/sync.py` é só o esqueleto com as regras
documentadas). Ver seção "Comandos manuais equivalentes" abaixo enquanto
isso não existe.

### `fix-cues` — corrige referências `.cue` → `.bin`

**Ainda não implementado** (`core/cues.py` é só o esqueleto). A lógica
manual que ele vai formalizar: o nome do `.cue` é a fonte da verdade, o(s)
arquivo(s) `FILE "..."` referenciado(s) dentro dele devem se chamar
`<nome do cue>.bin` (single-track) ou `<nome do cue> (Track N).bin`
(multi-track). Nunca mexe em `.ccd`/`.img` (formato diferente). Nunca
deleta `.cue` sem `.bin` correspondente.

## Interface gráfica (Fase 1)

```bash
python3 gui/server.py              # abre em http://localhost:8000
python3 gui/server.py --port 8080  # outra porta
```

Servidor local, stdlib só (`http.server`), sem dependência nova - mesma
filosofia do resto do projeto. Dá pra acessar do navegador do celular também,
se PC e celular estiverem na mesma rede (usa o IP da máquina em vez de
`localhost`).

O que tem até agora:
- Galeria pra navegar pelas capas de cada sistema
- Botões pra rodar `fetch-covers` e `fetch-covers-fallback` com progresso ao
  vivo (via Server-Sent Events), incluindo o toggle simulação/aplicar de
  verdade que os comandos de CLI já tinham

O que ainda não tem (fases futuras, ver conversa de planejamento): revisão
visual de fuzzy match lado a lado, telas de sync/fix-cues (esperando esses
comandos existirem de verdade), gestão de pastas/duplicatas.

## Comandos manuais equivalentes (enquanto `sync` não existe)

Cópias mais comuns entre PC e celular, via `adb`. Ajuste os caminhos aos
do seu `config.toml` se forem diferentes dos exemplos abaixo.

**Puxar saves do celular pro PC** (depois de uma sessão jogando no Android):
```bash
adb pull /storage/emulated/0/RetroArch/saves ~/Drive/Jogos/Saves/saves
adb pull /storage/emulated/0/RetroArch/states ~/Drive/Jogos/Saves/states
```

**Mandar saves do PC pro celular** (depois de jogar no PC):
```bash
adb push ~/Drive/Jogos/Saves/saves /storage/emulated/0/RetroArch/saves
adb push ~/Drive/Jogos/Saves/states /storage/emulated/0/RetroArch/states
```

**Sincronizar capas de um sistema específico pro celular** (depois de rodar
`fetch-covers`):
```bash
adb push "~/Drive/Jogos/Capas/Sony - PlayStation/Named_Boxarts" \
  "/storage/emulated/0/RetroArch/thumbnails/Sony - PlayStation/"
```

**Sincronizar TODAS as capas pro celular:**
```bash
cd ~/Drive/Jogos/Capas
for d in */; do
  sys="${d%/}"
  adb push "$sys/Named_Boxarts" "/storage/emulated/0/RetroArch/thumbnails/$sys/"
done
```

**Puxar o `retroarch.cfg` do celular pra conferir/editar:**
```bash
adb pull /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg \
  ~/Drive/Jogos/retroarch_android.cfg
```

**Mandar de volta depois de editar** (o caminho é dentro da pasta privada do
app - às vezes precisa primeiro mandar pra um caminho público e copiar por
dentro do celular, dependendo de como o ambiente que roda o comando lida com
permissão):
```bash
adb push ~/Drive/Jogos/retroarch_android.cfg \
  /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg
```

**Conferir se o celular está conectado e autorizado:**
```bash
adb devices -l
```

## Estrutura do projeto

```
PyRetro/
├── retrosync.py          # CLI (argparse) - ponto de entrada
├── config.example.toml   # template de configuração
├── config.toml           # sua config real (git-ignored)
├── core/
│   ├── covers.py          # busca/substituição de capas - implementado
│   ├── launchbox.py       # segunda fonte de capas (LaunchBox Games DB) - implementado
│   ├── sync.py            # sincronização PC<->Android - esqueleto
│   ├── cues.py             # correção de .cue - esqueleto
│   └── adb.py              # wrapper de adb com retry - esqueleto
├── gui/
│   ├── server.py          # servidor local da interface gráfica (Fase 1)
│   └── static/             # HTML/CSS/JS do frontend
├── docs/
│   └── capas_sem_correspondencia.md   # capas não resolvidas por nenhuma fonte
├── cache/
│   └── covers_registry.json   # histórico do que já foi processado por fetch-covers
└── logs/
```

## Status / próximos passos

| Módulo | Status |
|---|---|
| `core/covers.py` | Implementado e testado - resolve exato, fuzzy (só relatório), DAT do FBNeo pro Arcade, fallback de download via API do GitHub, distingue rate-limit de sem_match real |
| `core/launchbox.py` | Implementado e testado - segunda fonte (LaunchBox Games DB) só pros sem_match do covers.py, exato + prefixo com trava de segurança |
| `core/adb.py` | Esqueleto - `run`/`shell`/`push`/`pull`/`ensure_connected` documentados, não implementados |
| `core/sync.py` | Esqueleto - regras de "mais recente vence" e conflito documentadas, não implementado |
| `core/cues.py` | Esqueleto - regras de nomenclatura documentadas, não implementado |
| `retrosync.py` | Só `fetch-covers` conectado de verdade; `sync` e `fix-cues` levantam `NotImplementedError` |

Ordem sugerida pra continuar: `core/adb.py` primeiro (é a base que `sync.py`
vai precisar), depois `core/sync.py` (o mais pedido no dia a dia), `cues.py`
por último (uso mais pontual).
