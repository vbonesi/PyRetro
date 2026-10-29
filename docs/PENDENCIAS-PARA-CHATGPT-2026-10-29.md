# Pendências do PyRetro para continuar (ChatGPT/Codex) — 29/10/2026

Leia antes: `CLAUDE.md`/`AGENTS.md` (topo), `docs/nuvem.md`, `docs/armazenamento.md`, `docs/trabalho-em-conjunto.md`
e as entradas de 28–29/10 do `docs/changelog.md`. Responder sempre em português. O Victor é o dono das decisões.

## Regras que valem (aprendidas nesta rodada)

- **Saves de jogos finalizados nunca são apagados** (decisão do Victor, 29/10): ficam nos dois aparelhos e na nuvem, mesmo sem a
  ROM local. A ROM de um jogo finalizado pode sair do aparelho; o save não. Só apagar save quando o Victor pedir, jogo a jogo.

- **Nunca apagar nada do acervo/saves sem prova:** ROM só sai do PC/celular depois de `rclone check`/MD5 idêntico no
  Drive. Saves e estados de teste: comparar a lista de arquivos antes/depois e remover só o que o teste criou.
- **`~/Downloads` é um link para `~/Drive/Temp`:** nada que não deva ir à nuvem pode morar ali.
- **Não abrir `library.json`/`config.toml` à mão** (segredos e dado vivo); usar `retrosync.load_config()` e as APIs.
  O `config.toml` ganhou `[storage]` (raízes novas) e `[cloud]` (remoto, `auto = true`); cópias antes de editar em `auditoria/`.
- **Emuladores fechados** para mexer em config/saves; não usar `pkill -f` com padrão que apareça na própria linha de comando.
- **Celular um agente por vez** (`adb install --user 0 -r`); toolchain e comando de build em `CLAUDE.md`. Não tirar
  captura de tela da tela inteira do desktop (pega conteúdo pessoal); preferir `uiautomator dump`/capturas do aparelho.
- **Setup:** toda mudança na máquina também vai para `setup-linux-bonesi` + `docs/PENDENTE-CONSOLIDAR.md` (outra
  conversa/repositório; ela já registrou até a linha 20).
- Reiniciar `pyretro-gui` só com o modo TV fechado.

## Estado em 29/10 (resumo)

- Acervo em `~/Games/PyRetro` (ROMs, BIOS, NSW, Capas, Saves, Biblioteca, Backups); `[storage] migrated` inclui tudo.
  Local fica só com jogos em andamento; o resto vem do Drive sob demanda (PC e celular). ROMs de Arcade também saíram.
- Nuvem independente: `core/cloud.py`, `cloud_saves.py`, `cloud_sync.py`, `cloud_snapshots.py`, `library_journal.py`;
  remoto `drive:Jogos/PyRetro-Nuvem`; saves sincronizam antes/depois do jogo (`auto = true`).
- Android **0.19.0**: ficha 💾 Saves e "Saves e estados" usam só o motor de nuvem (testado no aparelho).
- Biblioteca: diário SQLite + snapshots; Backups sobem à nuvem sem Insync.

## Pendências (marcar `[x]` ao concluir)

### Em andamento / verificar primeiro
- [x] **Envio dos Backups à nuvem:** concluído em 29/10 (`publish_tree` agora paralelo; 505 arquivos locais, todos presentes
      em `drive:Jogos/PyRetro-Nuvem/backups`; conferido por `rclone size` e uma 2ª rodada sem pendência).
- [ ] **Insync (só o Victor):** desmarcar `Saves`, `Capas`, `Biblioteca` e `Backups` na sincronização seletiva. Antes,
      conferir `python3 -m core.cloud_sync status` = `{}` e que o último snapshot da Biblioteca está na nuvem.

### Celular independente do notebook (o que o Victor quer)
- [ ] **Biblioteca local no celular + diário em Kotlin:** portar `core/library_journal.py` (diff, apply, LWW por jogo/campo,
      segmentos imutáveis em `journal/<dispositivo>/`) para o app, com testes JVM de paridade (como `CloudSavesTest`).
      Base inicial = último `snapshots/library/latest.json` da nuvem (`DriveCloudStorage`).
- [ ] **Trocar a fila de progresso/tempo para o diário:** hoje o celular manda nota/iniciado/finalizado/tempo/favoritos por
      HTTP ao notebook (`StatusStore`/`pending`). Deve gravar no diário e subir pela nuvem; o notebook junta com
      `cloud_sync.pull_library` (já existe e é testado).
- [ ] **Agendar o `pull_library` no notebook** (ao iniciar, depois de cada jogo e a cada poucos minutos) e o equivalente
      no celular (WorkManager, respeitando bateria). Hoje é manual: `python3 -c "from core import cloud_sync..."`.
- [ ] **Relógio híbrido:** LWW usa `at` de cada aparelho; um relógio errado ganha edições indevidas. Guardar o maior `at`
      já visto e nunca usar um menor (PC e Android).
- [ ] **Catálogo sem o notebook:** montar a lista a partir da Biblioteca local + listagem direta das pastas do Drive
      (`CloudIndex`/`GoogleDrive`); hoje vem de `/api/tv/catalog`.
- [ ] **Capas sob demanda pela nuvem:** decidir com o Victor (recomendado: subir para `capas/` da nuvem só as dos jogos
      exibidos; as 2,1 GB de `Biblioteca/capas` não estão na nuvem e saem do Insync).
- [ ] **Remover de vez o que sobrou do protocolo antigo:** rotas `/api/mobile/sync/*` e `core/mobile_sync.py`
      (`core/game_save_ids.py` ainda usa `mobile_sync.accepted`; extrair essa regra antes), `docs/drive-saves.md` e
      `docs/mobile-save-ids.md` desatualizados.

### Saves / emuladores
- [ ] **Exclusão explícita de saves na nuvem (tombstone):** o motor nunca propaga exclusão (arquivo que falta é restaurado);
      apagar um save de verdade exigiu editar `saves/devices/*.json` à mão em 29/10. Criar a operação "esquecer" com teste
      PC/Android (e confirmação na tela).
- [ ] **Decidir sobre `Lime3DS/sdmc` do celular no PC:** 27 arquivos de 3DS do celular (Pokémon X/Y extdata, demo Epic
      Mickey, etc.) chegaram a `~/Games/PyRetro/Saves/Lime3DS/sdmc`. Perguntar se ficam ou se o 3DS sai da sincronização
      (`CloudSaves(..., exclude=...)` no PC; `CloudPhone.prefixes` no app).
- [ ] **Estados entre PC e celular:** `savestate_auto_load` com `.state.auto` vindo do outro aparelho pode carregar estado
      de core incompatível. Avaliar excluir `states/` da sincronização automática ou separar por dispositivo.
- [ ] **Zelda Molblins (DS):** o erro "write to your cart" some com um `.sav` em branco de 512 KB em
      `Saves/saves/NDS/` (já criado). Pedir ao Victor para confirmar jogando.
- [ ] **Conflitos de saves na tela:** hoje só no app (botões) e na rota `/api/cloud/saves/resolve`; falta a tela de
      conflito no modo TV do notebook.

### Controles
- [ ] **Galileo G8 no notebook:** `python3 tools/configure_xbox.py --learn galileo-g8` com SÓ ele conectado. Já medidos:
      Xbox One (principal), Series S ("Xbox Series X Controller") e WGP16 (aparece como "Sony Interactive Entertainment
      Wireless Controller", GUID 054c:09cc). Aplicar o perfil de outro controle: `--controller <id> --apply` (emuladores fechados).
- [ ] **Escolha automática do perfil pelo controle conectado** (Dolphin/Azahar dependem do modelo): hoje é manual; o
      lançador do setup poderia chamar `configure_xbox.py --detect/--controller`.

### Interface / produto
- [x] **Revisão comparativa Android × PC (Codex, 29/10):** matriz, divergências e roteiro reproduzível
      em `REVISAO-ANDROID-PC-2026-10-29.md`; 48 telas/estados no aparelho, em retrato/paisagem.
      As diferenças identificadas continuam abertas; navegação aprovada não comprova paridade.
- [ ] **Aplicar as diferenças da revisão Android:** primeiro erros/confirmações de saves, filtro de Desejados
      e Ranking em retrato; depois escopo PSP/3DS, glifos/foco/espaço útil e remoção local/Drive.
- [ ] **Testes automatizados do que só foi conferido no navegador:** pódio do Ranking, filtros recolhíveis, glifos
      Xbox/PS, tela "🗑 Remover…" (modo TV, `tests/test_app.html`).
- [ ] **Remoção na ficha:** confirmar uma remoção real de ponta a ponta (PC + Drive à lixeira) com um jogo descartável;
      até agora só a prévia foi exercitada. Ligar também ao Android (ficha) com a mesma regra de `core/removal.py`.
- [ ] **Identidade visual:** conferir os ícones nas máscaras do launcher do Android e no Steam Big Picture (instalados,
      mas não vistos nesses lugares). O recurso monocromático já existe em `ic_launcher.xml`; falta conferir o
      resultado do ícone temático no launcher. O cabeçalho Android ainda usa a estrela.
- [ ] **Arcade:** nenhum jogo atual depende de outro jogo (só de BIOS em `BIOS/RetroArch`). Se a coleção crescer, a
      resolução de pai (`core/arcade.py`) já baixa os pais; testar com um clone real quando houver.
- [ ] **Homologação física restante (Victor):** G8 e interrupção de download já testados por ele; ficam atalhos do 3DS e uso
      prolongado.

### Produto "para outras pessoas" (ideia futura, sem decisão)
- [ ] Escopo `drive.file` (app só vê o que criou) em vez de `drive` para terceiros; credenciais no chaveiro; outros
      provedores via rclone/`Storage`; empacotamento (Flatpak/AppImage) e onboarding. Ver `docs/nuvem.md`.
      Modelo "traga a sua nuvem"; não hospedar ROMs de terceiros.

## Como validar (rápido)

```bash
python3 -m unittest discover -s tests          # ~435 testes Python
# JS: abrir http://localhost:8000/tests/test_app.html e ler window.RESULTADO (54 testes)
JAVA_HOME=~/.cache/pyretro/android-toolchain/jdk ANDROID_HOME=~/.cache/pyretro/android-toolchain/sdk \
  python3 tools/build_android.py < /dev/null   # compila, roda JVM e lint; APK em cache/artifacts/
python3 -m core.cloud_sync status               # {} = tudo em dia com a nuvem
python3 -m core.storage                         # prévia de armazenamento (config bruto)
```
