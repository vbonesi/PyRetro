# Armazenamento do PC: acervo local sob demanda (etapa E, 28/10/2026)

## Atualização de 29/10

Todas as categorias migraram para `~/Games/PyRetro`, incluindo NSW, Saves, Capas, Biblioteca e Backups.
Biblioteca e saves usam a nuvem direta; Backups tiveram os 505 arquivos verificados por hash.
Estados novos são separados por dispositivo. As árvores remotas antigas com diretórios duplicados
foram preservadas e substituídas por árvores verificadas. Ver `nuvem.md` e a lista de pendências atual.
ROMs/BIOS já foram desmarcadas no Insync pelo Victor; as outras quatro pastas aguardam ação dele.
Não apagar dados dentro de `~/Drive`. Limpezas posteriores solicitadas pelo Victor continuam válidas.
O relato abaixo registra a migração de 28/10 e não representa pendências atuais.

## Histórico da migração de 28/10

Estado (28/10, noite): **etapa (a) feita**: ROMs (sem NSW) e BIOS copiados para `~/Games/PyRetro`
com SHA-256 conferido na origem e no destino (1.915 arquivos, 41,7 GB, 0 erros; recibo em
`~/Games/PyRetro/.pyretro/receipts/`). O Drive está intacto e **nada foi desmarcado no Insync**.
NSW, Saves, Capas, Biblioteca e Backups ainda não foram copiados. Copiar de novo:
`python3 -m core.storage --copy roms,bios` (idempotente, nunca sobrescreve). O que
existe: `core/storage.py` (resolvedor de destinos `Layout` e `plan`) e `tests/test_storage.py`.
Plano completo: [`plano-melhorias-2026-10-28.md`](plano-melhorias-2026-10-28.md), seções 5 a 8.

## Situação em 28/10 (noite)

- **ROMs e BIOS religados.** `[storage]` no `config.toml` (`games_root`, `migrated = ["roms", "bios"]`)
  faz `retrosync.load_config()` e o servidor usarem `~/Games/PyRetro/ROMs`; saves, capas,
  biblioteca e backups seguem no Drive. `pc.nsw_root` aponta para o NSW antigo enquanto ele não migrar.
  Cópia privada da configuração anterior em `auditoria/config-antes-storage-*.toml`.
- **Playlists do RetroArch regeneradas** pelo layout novo (13 sistemas); cópia das antigas em
  `Backups/playlists-antes-storage-*`. Dreamcast, Saturn e Neo Geo (CD) têm entradas antigas de
  ROMs que já não existem em lugar nenhum; ficaram como estão.
- **Emuladores abertos pelo caminho novo** (lançador, 28/10): SNES, DS, PS1, PSP, GameCube, 3DS e PS2
  iniciaram e ficaram rodando. Isso prova abrir, não o ciclo de save de cada um.
- **NSW em `~/Games/PyRetro/NSW`** (decisão do Victor): `~/Downloads` é um link para `~/Drive/Temp`,
  então `~/Downloads/NSW` seria sincronizado pelo Insync; a prévia agora bloqueia isso (resolve
  links). O título local (3 arquivos, 3,5 GB) foi copiado e verificado por hash, e `nsw` entrou em
  `migrated`.
- **`ROMs` e `BIOS` já desmarcadas** pelo Victor (28/10); nuvem manteve tudo.
- **Setup (g) de ROM/BIOS aplicado** (`7e89d27` no setup): DuckStation sem a 2ª `RecursivePaths`,
  Dolphin com `ISOPaths = 2`, lançador só com `~/Games/PyRetro/ROMs`. Overrides do Flatpak
  `Drive/Jogos:ro` e `Saves/*` continuam até a etapa G; cópia dos configs em
  `~/.local/state/bonisarch/backups/paths-20261028-190408`.
- **Capas migrada (28/10):** 1.931 arquivos copiados e verificados; `migrated` inclui `capas`; os links
  dos emuladores foram refeitos pela manutenção. Pronta para desmarcar no Insync (só pelo Victor).
- **Biblioteca, Backups e Saves ficam no Drive de propósito, por ora:** o Drive é hoje a rede de
  segurança de cada uma (histórico de versões do `library.json`, cópia fora do disco dos backups e
  transporte dos saves). Tirar do Drive exige antes o substituto: snapshot versionado da
  Biblioteca, backup remoto verificável e a etapa G (saves direto pelo Drive, que pede rclone com
  escrita). Ver `plano-melhorias-2026-10-28.md`, seções 5.4 e 5.5.

## Ver a prévia (somente leitura)

```bash
python3 -m core.storage            # resumo legível
python3 -m core.storage --json     # tudo, para conferir item a item
```

Prévia de 28/10 (acervo local de hoje): 7.610 arquivos, **49 GB** (ROMs 45 GB), 174 GB livres,
nenhum bloqueio e nenhum aviso. Os valores mudam; rode de novo antes de decidir.

## Layout alvo

| Hoje | Depois |
|---|---|
| `~/Drive/Jogos/ROMs/<sistema>` | `~/Games/PyRetro/ROMs/<sistema>` |
| `~/Drive/Jogos/ROMs/NSW/<título>` (e arquivos soltos, agrupados por nome sem tags) | `~/Downloads/NSW/<título>` |
| `~/Drive/Jogos/Saves` (saves, states, runtime-logs, PPSSPP, Lime3DS, DuckStation, PS2, Dolphin) | `~/Games/PyRetro/Saves` |
| `Capas`, `Biblioteca`, `Backups`, `BIOS` | mesmo nome dentro de `~/Games/PyRetro` |

O código do PyRetro (`~/Drive/Jogos/PyRetro`) **não** muda de lugar. Outras pastas de `~/Games`
(Heroic, dlc-unlocker) e de `~/Downloads` ficam fora.

## Regras da migração (H)

1. **Sempre copiar e verificar, nunca `mv`**: apagar dentro de `~/Drive` apaga a cópia da nuvem.
2. Só depois da cópia verificada e dos consumidores ajustados o Victor desmarca a pasta na
   sincronização seletiva do Insync (nunca `rm` dentro do Drive). O Claude avisa pasta por pasta.
3. Raízes novas fora do Drive; bloqueia se estiverem dentro dele ou uma dentro da outra.
4. Destino já existente é conferido, não sobrescrito. Links simbólicos são listados, não seguidos.
5. CUE/GDI/M3U com faixa ausente aparecem como aviso (o conjunto é copiado inteiro, nunca partido).
6. Ordem: ROMs (piloto com um leve e um conjunto pesado) → NSW → Saves (depende de G) → metadados.

## Quem ainda aponta para a pasta antiga (setup)

- `~/.local/bin/bonisarch-emulator` só aceita ROM dentro de `~/Drive/Jogos/ROMs`.
- Overrides do Flatpak: PCSX2 (`Saves/PS2` e `Jogos:ro`), Dolphin e PPSSPP (`Jogos:ro`), Azahar
  (`Saves/Lime3DS`). RetroArch não tem override listado.
- Pedido enviado à conversa do setup em 28/10 (planejar sem aplicar); registrar o resultado em
  `setup-linux-bonesi/docs/PENDENTE-CONSOLIDAR.md`.

- Conferido pelo setup em leitura (28/10): o **PCSX2** tem `Bios`, `Savestates`, `MemoryCards`,
  `InputProfiles` e `GameSettings` em `~/Drive/Jogos` (BIOS/PS2 e Saves/PS2); ao migrar a BIOS ele
  também precisa trocar `Bios`. O **PPSSPP** não guarda pasta de ROMs; só o histórico `[Recent]`
  aponta para a pasta antiga. Os dois são Flatpak (`~/.var/app/...`). RetroArch, DuckStation e
  Dolphin guardam caminhos de ROMs, saves e BIOS; as playlists `.lpl` do RetroArch têm caminhos
  absolutos e serão regeneradas pelo PyRetro (com backup) na etapa de religar os emuladores.
- **Teste do Insync (Victor, 28/10): desmarcar uma pasta APAGA a cópia local** (a nuvem fica). É o
  comportamento "só nuvem" esperado, e por isso a cópia verificada em `~/Games/PyRetro` vem
  sempre antes de desmarcar qualquer categoria.

## Celular

O app já baixa sob demanda: o Catálogo mostra "↓ Baixar" e a ROM vem do Drive, em segundo plano,
só quando você toca. A gestão que falta é a de espaço (seleção local, iniciados protegidos,
remover só deste celular, Drive à lixeira): etapa F do plano.

## Rollback

Enquanto nada foi desmarcado no Insync, o acervo original continua intacto: basta não apontar os
consumidores para o novo caminho. Depois de desmarcar, reconciliar saves antes de voltar, sem
sobrescrever um save novo com um snapshot antigo.

## Remoção local/Drive (etapa F, regras prontas)

`core/removal.py`: prévia e aplicação de três ações (`local`, `drive` = lixeira do Drive, `both`),
com proteção (iniciado/fixado/em execução), arquivos compartilhados preservados, aviso de última
cópia, token de revalidação, frase de confirmação com local e Drive por extenso e resultado por
item. Saves, estados, texturas, capa e cadastro nunca são tocados. **Rotas no servidor (28/10):**
`GET /api/storage/removal-plan?scope=local|drive|both&code=&entry=` e `POST /api/storage/removal-apply`
(`scope, code, entry, token, confirm`). Falta a interface (ficha do jogo). O Drive só funciona depois de reconectar o rclone com permissão de
escrita. **Reconectado em 28/10** (`scope = drive`; gravar e mandar à lixeira testados com um arquivo
descartável; o `deletefile` vai para a lixeira, não apaga de vez) e `[rclone] can_write = true` no
`config.toml`: a prévia do Drive já lista as cópias reais. Sem a escrita a prévia bloqueia a ação.

## Política de espaço (Victor, 28/10): só os jogos em andamento ficam; o resto sob demanda

- **PC, feito em 28/10:** apagadas as ROMs pesadas (PS, PS2, GameCube, Wii, PSP, 3DS) e o NSW de
  `~/Games/PyRetro`, só depois de `rclone check` provar cópia idêntica (hash) no Drive: 20 arquivos,
  20,5 GB. Ficaram as 4 pesadas dos jogos em andamento (Gran Turismo 2, Toy Story Racer, Guitar Hero
  III, NFS Underground 2). O PyRetro continua listando os apagados para baixar.
- **PC, ROMs leves (feito em 28/10, à noite):** o catálogo do Drive, o download, o sorteio e a lista do modo TV
  passaram a cobrir também os sistemas leves; provado ponta a ponta (apagar, baixar pela rota, mesmo
  hash). Apagados 1.318 arquivos (16,3 GB) de FC, SFC, GB, GBC, GBA, N64, NDS, MD, SMS, GG, PCE e
  PCECD, todos com cópia idêntica no Drive. Ficaram Final Fantasy VI, Super Mario 64, Kirby's
  Adventure e o Molblins. **O Arcade ficou inteiro (3,2 GB):** clones precisam dos zips "pai"/BIOS e
  baixar um jogo sozinho o deixaria sem rodar. Playlists dos sistemas esvaziados foram zeradas (cópia
  em `Backups/playlists-antes-leves-*`). Restaurado a pedido o Castlevania SotN (era o sorteado).
- **Celular, feito:** 12 ROMs apagadas de `/sdcard/Jogos` depois de MD5 igual ao do Drive (3,9 GB → 0,4 GB,
  o resto é dado de emulador). Ficaram FF VI, Super Mario 64 (em andamento) e o Zelda Molblins.
- "O que foi sorteado" não é registrado em lugar nenhum; ficaram os jogos em andamento (biblioteca) e o
  Molblins. O último jogo aberto no PC (Kirby's Adventure, FC) é leve e também ficou.

## Saves migrados para ~/Games/PyRetro/Saves (28/10, noite)

- Cópia verificada (418 arquivos) e **todos os 405 conteúdos distintos já estão na nuvem**
  (`drive:Jogos/PyRetro-Nuvem/saves`, 0 erros). Nada diferia entre o Drive e a cópia no momento da troca.
- Aplicado (setup `install-emulator-library.py --saves`, cópia em `~/.local/state/bonisarch/backups/paths-20261028-202843`):
  RetroArch (saves/states), DuckStation, PCSX2 e o link do sdmc do Azahar apontam para `~/Games/PyRetro/Saves`.
  Dolphin e PPSSPP usam as próprias pastas de dados (nada a trocar).
- PyRetro: `[storage] migrated` inclui `saves`; `memcards.*` do `config.toml` apontam para a pasta nova.
- **Falta (Victor):** abrir um jogo com save em cada emulador e conferir que o save aparece em
  `~/Games/PyRetro/Saves`. Só depois: `install-emulator-access.py --sem-drive --apply` (setup), `[cloud] auto = true`
  e desmarcar `Saves` e `Capas` no Insync. Reverter: restaurar a cópia dos configs do setup e `migrated` sem `saves`.
