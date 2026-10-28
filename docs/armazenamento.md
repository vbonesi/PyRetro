# Armazenamento do PC: acervo local sob demanda (etapa E, 28/10/2026)

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
- **Pronto para desmarcar no Insync, só pelo Victor: `ROMs` e `BIOS`** (cada uma, nunca `Jogos`).
  Tudo que elas tinham está em `~/Games/PyRetro` com hash conferido.

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
item. Saves, estados, texturas, capa e cadastro nunca são tocados. **Ainda não está ligado ao
servidor nem à interface** e o Drive só funciona depois de reconectar o rclone com permissão de
escrita (hoje é somente leitura, e a prévia bloqueia a ação com essa explicação).
