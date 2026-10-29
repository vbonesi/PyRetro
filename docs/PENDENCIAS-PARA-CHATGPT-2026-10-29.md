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

## Estado final da implementação em 29/10

Android **0.22.0 / code 32**. Acervo em `~/Games/PyRetro`; todas as categorias migradas.
Biblioteca local com SQLite/diário no PC e Android, nuvem direta e capas dos jogos exibidos.
Saves compartilhados; estados separados por dispositivo. O protocolo HTTP/Insync antigo foi retirado.
As limpezas de jogos/saves feitas pelo Claude a pedido do Victor continuam válidas: não restaurar esses dados.

## Entregas concluídas

- [x] **Backups:** 505 arquivos conferidos por hash. A contagem inicial escondia diretórios duplicados
  no Drive, criados por uploads concorrentes. Árvores novas verificadas foram promovidas para
  `backups/` e `states/`; os diretórios anteriores ficaram em `*-preservado-20261029-*`, sem apagar cópias.
  Os nove objetos de estados foram preservados e conferidos. Escritas agora serializam a criação de
  diretórios e o mesmo caminho; uploads de caminhos diferentes continuam paralelos. Teste concorrente aprovado.
- [x] **Biblioteca independente:** SQLite transacional Android, bootstrap por snapshot, diário imutável
  Kotlin/Python, relógio persistente, desempate por campo e replay idempotente. Progresso, favoritos e novas
  sessões entram no diário; pendências antigas identificadas migram sem contar tempo duas vezes.
  Conflitos antigos e entradas sem identidade ficam preservados. Desejados, estatísticas, cadastro e edição
  usam a Biblioteca local; serviços externos continuam exigindo conexão.
- [x] **Agendamento:** PC recebe no início, pós-jogo e a cada cinco minutos; Android usa WorkManager
  com rede/bateria suficiente, período mínimo de 15 minutos e limitações normais do sistema.
- [x] **Catálogo e capas:** Biblioteca + pastas do Drive, incluindo jogos sem cadastro e ambiguidades explícitas.
  Nomes/dependências de Arcade vêm do DAT local publicado como metadados, sem enviar ROM/BIOS.
  Capas enviadas somente quando exibidas, com SHA-256, ponteiro por jogo e cache offline.
  Prova real de uma capa passou por envio/leitura e igualdade de bytes.
- [x] **Protocolo antigo:** rotas `/api/mobile/sync/*` retornam 410, módulo antigo retirado e validação
  extraída para `core/save_paths.py`; documentação do protocolo atualizada.
- [x] **Saves:** falhas preservam a tela e permitem repetir; TV e Android exibem conflitos e versões.
  PSP/3DS usam identificação verificada/escolhida por título, região e árvore. Sem identificação há
  opção explícita de todos os jogos do emulador. Extdata não é inferida pelo Program ID.
- [x] **Esquecer um save:** operação individual com confirmação e revalidação, marcador `deleted` do protocolo v2,
  histórico local e blobs preservados. Cópia inalterada de outro aparelho acompanha o marcador;
  edição offline vira conflito. Restaurar cria uma versão normal. Nenhuma exclusão em lote ou por jogo finalizado.
- [x] **3DS e estados:** manter saves/extdata compartilhados, como escolhido pelo Victor; novos estados em
  `states/<dispositivo>`. Android usa identidade persistente própria. Não ressuscitar os saves antigos removidos.
- [x] **Molblins:** encerrado por remoção solicitada pelo Victor; não homologado em jogo e não deve ser recriado.
- [x] **Remoção de ROM:** Android oferece celular/Drive/ambos, prévia, revalidação e proteção de iniciados,
  fixados, execução/fila e arquivos compartilhados. Lixeira local recuperável e lixeira do Drive.
  Prova real PC/Drive usou ROM sintética própria; prova SAF Android verificou remoção e restauração idêntica.
  Arcade bloqueia quando o índice de dependências é incompleto.
- [x] **Controle automático:** `configure_xbox.py --auto --apply` e lançador do setup selecionam apenas
  um controle medido, com emuladores fechados; nove testes do configurador e nove do lançador aprovados.
- [x] **Diferenças Android × PC:** Desejados, Ranking 1–2–3 em retrato/2–1–3 em paisagem, desempates,
  glifos automáticos/manuais, foco distinto da seleção, abas visíveis, espaço útil, ajuda, marca PR,
  nota 11, sorteio repetido, selos e indicação da fila foram aplicados. Histórico da revisão em
  `REVISAO-ANDROID-PC-2026-10-29.md`; resultados físicos finais registrados ali.
- [x] **BIOS Neo Geo:** `neogeo.zip` em `/sdcard/RetroArch/system/fbneo/`, MD5 igual ao PC.
  FBNeo iniciou KOF '97 sem arquivos faltantes e exibiu o boot Neo Geo. Configuração original inalterada;
  saves/estados/logs do teste ficaram em pasta própria, removida ao terminar.

## Pendências que exigem ação ou equipamento do Victor

Fechadas pelo Victor em 29/10 (não reabrir): Insync com `Saves`, `Capas`, `Biblioteca` e `Backups`
desmarcados; ícone temático; BIOS do Neo Geo no celular; Arcade com clone real.

- [ ] **Galileo G8 no notebook:** medir com só ele conectado: `python3 tools/configure_xbox.py --learn galileo-g8`.
  Alternância física dos perfis ainda não homologada.
- [ ] **3DS:** atalhos em jogo e uso prolongado. Os jogos removidos não devem ser baixados para isso.
- [x] **KOF '97 (Arcade pelo título completo):** conferido pelo Victor em 29/10 (capa no app e tempo no PC).
  Regra única em `library.rom_name_keys`/`records_for_rom`/`find_for_rom`; testes em `tests/test_arcade_titles.py`.
- [x] **Pastas antigas do Drive (`Jogos/Saves`, `Jogos/Biblioteca`, `Jogos/Backups`):** resolvidas pelo Victor em 29/10
  (comparadas por hash antes, sem perda).

## Ideias futuras, sem decisão de implementação

- [ ] Produto para terceiros: escopos/OAuth, chaveiro, provedores adicionais, Flatpak/AppImage e onboarding.
- [ ] Distribuir BIOS sob demanda pela nuvem. A correção atual usa a BIOS local já existente do Victor.

## Validação reproduzível

```bash
python3 -m unittest discover -s tests
# Navegador, acervo sintético: /tests/test_app.html; conferir #resumo (58 testes).
JAVA_HOME=~/.cache/pyretro/android-toolchain/jdk ANDROID_HOME=~/.cache/pyretro/android-toolchain/sdk \
  python3 tools/build_android.py < /dev/null
# Compilar também :app:assembleDebugAndroidTest; instalar ambos com --user 0 -r.
adb shell am instrument -w -e suite interface com.pyretro.app.test/com.pyretro.app.StorageSmoke
python3 -m core.cloud_sync status
```
