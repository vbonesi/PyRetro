# Rodar o PyRetro direto no Android (Termux) - passo a passo

Modo experimental, ainda não testado de verdade contra o aparelho (é o
"modo Android" previsto em [`docs/roadmap.md`](roadmap.md) "Arquitetura
de dois modos"). Documentado como ponto de partida - espera relato de
uso real pra virar suportado de verdade.

## O que funciona nesse modo, o que não funciona

`gui/server.py` é stdlib puro - a única dependência externa real é o
`convert` do ImageMagick (`curl` também, mas geralmente já vem no
Termux). Rodando local no aparelho:

- **Funciona igual**: galeria de capas, busca visual, marcar
  errada/duplicada, renomear com cascata, organizar `0-Organizar`,
  configurações - tudo isso é operação de arquivo local, não depende
  de rede nem de `adb`.
- **Não se aplica** (e vai dar erro/não aparecer, sem quebrar o resto):
  qualquer coisa que dependa de `core/adb.py` - o app já está rodando
  onde os arquivos estão, não tem "outro lado" pra falar via adb. Os
  botões que hoje mostram status "no celular"/"só no PC" no modal de
  ROMs Pesadas não fazem sentido nesse modo (o próprio app já É o
  celular).
- **Não mapeado ainda**: consumo de bateria com o servidor rodando em
  segundo plano, e a melhor forma de abrir a interface (ver seção
  final).

## Passo a passo

1. **Instalar o Termux** - pela [F-Droid](https://f-droid.org/packages/com.termux/),
   não pela Play Store (a versão da Play Store está desatualizada e sem
   suporte há anos).

2. **Dar acesso ao armazenamento**, dentro do Termux:
   ```bash
   termux-setup-storage
   ```
   Aceita a permissão que o Android pedir. Isso cria `~/storage/` com
   atalhos pras pastas reais do aparelho (`~/storage/shared/`,
   `~/storage/dcim/` etc).

3. **Atualizar pacotes e instalar o necessário**:
   ```bash
   pkg update && pkg upgrade
   pkg install python git imagemagick curl
   ```

4. **Clonar o PyRetro**:
   ```bash
   cd ~
   git clone https://github.com/vbonesi/PyRetro
   cd PyRetro
   ```

5. **Configurar o `config.toml`** - copia o exemplo e ajusta os
   caminhos pra apontar pro que já está sincronizado no aparelho via
   Google Drive (confirma o caminho real do app do Drive no seu
   Android antes - varia por app/versão, mas costuma ser algo dentro de
   `/storage/emulated/0/...`):
   ```bash
   cp config.example.toml config.toml
   ```
   Edita `[pc]` pros caminhos locais do Android (mesma estrutura de
   sempre, só que agora "pc" É o próprio celular):
   ```toml
   [pc]
   roms_root         = "/storage/emulated/0/.../Jogos/ROMs"
   capas_root        = "/storage/emulated/0/.../Jogos/Capas"
   saves_root        = "/storage/emulated/0/.../Jogos/Saves/saves"
   states_root       = "/storage/emulated/0/.../Jogos/Saves/states"
   runtime_logs_root = "/storage/emulated/0/.../Jogos/Saves/runtime-logs"
   organizar_dir     = "0-Organizar"
   ```
   A seção `[android]` (jogos_root/thumbnails_root/etc) e qualquer coisa
   que dependa de `adb` fica sem uso nesse modo - pode deixar como está
   no exemplo, só não vai ser chamada.

6. **Rodar o servidor**:
   ```bash
   python3 gui/server.py --port 8000
   ```

7. **Abrir no navegador do próprio celular**: `http://localhost:8000`.

## Manter rodando em segundo plano

Por padrão, fechar o Termux (ou o Android matar o app em background)
derruba o servidor. Duas opções, não testadas ainda:

- **`termux-wake-lock`** antes de rodar o servidor - impede o Android
  de suspender a CPU do Termux, mas não impede o app de ser fechado
  manualmente.
- **Termux:Boot** (app separado, também via F-Droid) - permite rodar
  um script automaticamente. Precisaria de um script em
  `~/.termux/boot/` chamando o servidor.

Nenhuma das duas foi testada nesta pesquisa - fica como próximo passo
quando alguém (você) testar de verdade no aparelho.

## Acesso rápido

Pra não digitar o comando toda vez, um atalho simples: cria um script
`~/pyretro.sh`:
```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/PyRetro && python3 gui/server.py --port 8000
```
```bash
chmod +x ~/pyretro.sh
```
E roda com `~/pyretro.sh`. O app **Termux:Widget** (também F-Droid)
permite colocar isso como atalho na tela inicial, mas não foi testado
aqui.
