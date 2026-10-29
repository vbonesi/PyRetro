# PyRetro como única interface de TV — orientação para o setup (29/10/2026)

Decisão do Victor: **deixar de usar o Plasma Bigscreen** (modo TV do KDE). O PyRetro (`/tv`, janela nativa
`gui/app.py`) já abre todos os apps de jogo do sistema. Quem executa esta lista é a conversa do
`setup-linux-bonesi`; o PyRetro já está pronto do lado dele (commit com a janela nativa e este documento).

## O que o PyRetro já faz

- `tools/pyretro-tv.sh` (link `~/.local/bin/pyretro-tv`, `.desktop` `pyretro-tv`, atalho da Steam): abre a janela
  nativa **em tela cheia**; uma segunda chamada não abre outra janela, só a traz para a frente (trava em
  `$XDG_RUNTIME_DIR/pyretro-tv.lock`). Classe da janela no KWin: `pyretro-tv`.
- Apps abertos pela tela de apps, conferidos em 29/10 pelo KWin (todos `fs=true`, 1920×1080):
  Steam em Big Picture (`steam://open/bigpicture`), Heroic em Console Mode (`--console --fullscreen`),
  PCSX2 e DuckStation em Big Picture (`-bigpicture -fullscreen`), PPSSPP (`--fullscreen`), RetroArch (`-f`).
  Jogos abertos pelo PyRetro continuam passando pelo `bonisarch-emulator` (tela cheia por emulador).
  Dolphin e Azahar não têm modo sem jogo; abrem pela janela normal.

## O que o setup precisa mudar

1. **Botão Guide/PS abre o PyRetro.** Hoje `assets/tv/bonisarch-tv-controller` só escuta dispositivos
   `vendor == 0x045e` com “xbox/microsoft” no nome e chama `bonisarch-tv --tv` (Bigscreen). Trocar por:
   - escutar também o **WGP16 Nova II**, que se apresenta como DualShock 4 (`vendor 0x054c`, `product 0x09cc`,
     SDL “Sony Interactive Entertainment Wireless Controller”, GUID em `assets/controllers/controllers.json`).
     O botão PS chega como `BTN_MODE` no nó de gamepad (não nos nós “Motion Sensors”/“Touchpad”):
     filtrar por `BTN_MODE in dev.capabilities()[EV_KEY]`, não só pelo nome;
   - no `BTN_MODE` (valor 1), executar `~/.local/bin/pyretro-tv` (ele abre em tela cheia ou só traz a janela
     existente). Sem a lógica de “voltar à tela inicial do Bigscreen” e sem suspender o remapeamento por foco;
   - manter o serviço `bonisarch-tv-controller.service` com outro nome (sugestão: `pyretro-guide`) e remover
     o antigo, sem deixar duas unidades ouvindo o mesmo botão.
2. **Remover o Bigscreen** de `step_tv_mode`: pacote `plasma-bigscreen`, `bonisarch-tv`,
   `plasma-bigscreen-swap-session`, `bonisarch-tv-shell/input.service`, `bonisarch-tv-games-only`,
   `-layout`, `-session`, `tv-focus.js`, atalhos “Modo TV”/“Voltar à área de trabalho” e o filtro
   `applications-blacklistrc`. Manter `bonisarch-emulator` (o PyRetro o usa).
3. **Steam/Heroic**: remover o encaminhamento de Exec para `bonisarch-tv-app` (só servia ao Bigscreen); os
   `.desktop` voltam ao original do Flatpak. O PyRetro abre os dois com os argumentos acima.
4. **Pacote novo**: `python-pyqt6-webengine` (já instalado nesta máquina em 29/10).
5. **Só depois** de o Victor validar o controle com a janela nativa: remover o override do Chrome Flatpak
   `/run/udev:ro` (era só para a Gamepad API do `/tv` no Chrome). Se a janela nativa falhar com o controle,
   `PYRETRO_TV_CHROME=1 pyretro-tv` volta ao Chrome sem alterar código.
6. Registrar tudo em `docs/PENDENTE-CONSOLIDAR.md` e atualizar `docs/MODO-JOGOS-NITRO.md`
   (hoje descreve o Bigscreen como entrada principal).

Não mexer em: saves, Steam VDF/atalhos pessoais, controles dos emuladores (`step_xbox_controls`).
Antes de desinstalar o Bigscreen, sair da sessão TV (`bonisarch-tv --desktop`) e conferir `--status`.
