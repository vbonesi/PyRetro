#!/usr/bin/env python3
"""
PyRetro GUI - Fase 1: galeria de capas + disparo de fetch-covers com
progresso ao vivo. Servidor local, stdlib só (http.server), sem
dependência nova - mesma filosofia do resto do projeto.

Uso:
    python3 gui/server.py [--port 8000]

Abre http://localhost:8000 no navegador. Se quiser acessar do celular,
use o IP da máquina na rede local em vez de localhost (as duas pontas
precisam estar na mesma rede).
"""
import base64
import bisect
import copy
import json
import queue
import re
import subprocess
import sys
import threading
import tomllib
import traceback
import unicodedata
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import adb as adb_mod
from core import config_backup as config_backup_mod
from core import covers as covers_mod
from core import emu_saves as emu_saves_mod
from core import emu_sync as emu_sync_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import library as library_mod
from core import memcard as memcard_mod
from core import organize as organize_mod
from core import pc_backup as pc_backup_mod
from core import playlist as playlist_mod
from core import rom_rename as rom_rename_mod
from core import sanitize as sanitize_mod
from core import screenscraper as screenscraper_mod
from core import serials as serials_mod
from core import sortear as sortear_mod

CONFIG_PATH = ROOT / "config.toml"
REGISTRY_PATH = ROOT / "cache" / "covers_registry.json"
HEAVY_CATALOG_PATH = ROOT / "cache" / "heavy_catalog.json"
# {nome limpo: nome real da pasta} do Switch - listar a NSW inteira via
# rclone leva minutos, inviável num clique da tela, então o mapa fica
# cacheado e é atualizado junto com "🔄 Switch"/library-refresh switch.
SWITCH_PASTAS_PATH = ROOT / "cache" / "switch_pastas.json"
STATIC_DIR = Path(__file__).parent / "static"

COVERS_EXCLUDED = covers_mod.COVERS_EXCLUDED

_jobs: dict[str, "queue.Queue"] = {}
_jobs_lock = threading.Lock()

# Serializa TODO ciclo ler-modificar-gravar do library.json. A GUI é
# multi-thread (ThreadingHTTPServer) e ainda pode ter job de fundo
# mexendo no mesmo arquivo (library-refresh, fetch-covers) enquanto o
# usuário clica na tela pelo celular - sem isso, duas escritas
# simultâneas viram "lost update": as duas carregam a mesma versão, e a
# última a gravar apaga a alteração da outra (ex: marcar "finalizado"
# some sozinho). A gravação em si já é atômica (ver
# core/library.save_library); esta trava cuida do outro lado, que é a
# leitura ficar consistente com a escrita que vem depois.
_library_lock = threading.RLock()


def _start_job(worker) -> str:
    """Cria um job genérico rodando `worker(emit)` em thread separada -
    `emit(dict)` empilha um evento na mesma fila/stream SSE que
    /api/fetch/stream já serve (genérico por job_id, não olha o tipo).
    Qualquer exceção não tratada dentro de `worker` vira um evento
    "error" em vez de derrubar o servidor; "job_done" sempre é emitido
    por último, mesmo em erro, pra quem está ouvindo saber que acabou."""
    job_id = f"job-{threading.get_ident()}-{id(object())}"
    q: "queue.Queue" = queue.Queue()
    with _jobs_lock:
        _jobs[job_id] = q

    def emit(event: dict) -> None:
        q.put(event)

    def run():
        try:
            worker(emit)
        except Exception as e:
            emit({"type": "error", "message": str(e)})
        finally:
            emit({"type": "job_done"})

    threading.Thread(target=run, daemon=True).start()
    return job_id

# "code:ss_id" -> media_url real do ScreenScraper (com credenciais
# embutidas) - NUNCA mandado pro cliente, só usado pelo proxy de
# preview e pelo download final. Em memória, por processo - some ao
# reiniciar o servidor, o que é aceitável (busca de novo re-popula).
_ss_media_cache: dict[str, str] = {}


def arcade_romname_dat(code: str) -> dict | None:
    """Nome de exibição do Arcade (romset curto -> título completo,
    ver core.covers.arcade_display_name) - só pra ARCADE, e nunca
    deixa uma falha de rede derrubar quem chama (diferente de
    core.covers.load_romname_dat, chamada aqui fora do contexto de job
    em background que já tem seu próprio try/except)."""
    if code not in covers_mod.ROMNAME_DATS:
        return None
    try:
        dat_url, dat_cache_name = covers_mod.ROMNAME_DATS[code]
        return covers_mod.load_romname_dat(dat_url, dat_cache_name)
    except Exception:
        return None


def light_rom_display_names(code: str, info: dict, roms_root: Path) -> list:
    """Nomes de exibição (display_name se Arcade, senão o nome do
    arquivo sem extensão) de toda ROM local de `code` - mesmo valor
    que a galeria de capas usa como "nome do jogo" pra cruzar com a
    Biblioteca (ver biblioteca_info em /api/covers)."""
    names = playlist_mod.list_local_names(code, roms_root, info.get("exts", []))
    romname_dat = arcade_romname_dat(code)
    out = []
    for n in names:
        label = Path(n).stem
        display = covers_mod.arcade_display_name(label, romname_dat) if romname_dat else None
        out.append(display or label)
    return out


def nome_de_arquivo_seguro(nome: str) -> bool:
    """True se `nome` pode virar nome de arquivo sem escapar da pasta
    de destino. Achado 28/08 numa auditoria: os endpoints de capa
    montavam o caminho com `capas_dir / f"{label}.png"` usando o label
    que veio da requisição, sem nenhuma checagem - um label com "../"
    escrevia FORA da pasta de capas (o servidor escuta em 0.0.0.0, ou
    seja, qualquer um na rede local conseguiria). Só falhou no teste
    por acaso, porque a contagem de "../" caiu numa pasta inexistente.
    Recusa separador de diretório, "..", nome vazio e caminho absoluto."""
    if not nome or nome in (".", ".."):
        return False
    if "/" in nome or "\\" in nome or "\x00" in nome:
        return False
    return True


def dentro_de(base: Path, alvo: Path) -> bool:
    """True se `alvo` (depois de resolvido) está dentro de `base` -
    segunda linha de defesa pra caminho montado a partir de entrada do
    usuário, ver nome_de_arquivo_seguro. Usa resolve() nos dois lados
    pra não ser enganado por symlink ou "..".."""
    try:
        base_r, alvo_r = base.resolve(), alvo.resolve()
    except OSError:
        return False
    return base_r == alvo_r or base_r in alvo_r.parents


def com_versao(url: str, arquivo: Path) -> str:
    """`url` + "?v=<mtime>" - achado 28/08: trocar a capa de um jogo
    parecia não funcionar ("não é possível substituir capa"). O arquivo
    ERA substituído no disco, mas /images e /library-images servem sem
    nenhum header de cache, então o navegador continuava mostrando a
    imagem antiga (cache heurístico) - a URL era idêntica, ele não
    tinha motivo pra buscar de novo. Com o mtime na query, trocar o
    arquivo troca a URL e o navegador busca; arquivo que não mudou
    mantém a URL e segue cacheado (importante: a galeria tem centenas
    de imagens, desligar cache pra todas seria pior)."""
    try:
        return f"{url}?v={int(arquivo.stat().st_mtime)}"
    except OSError:
        return url


def rom_normalized_names_by_code(cfg: dict) -> dict:
    """{codigo: {nomes normalizados}} de TODA ROM que existe de verdade
    - leve (arquivo local, todo sistema) + pesada (catálogo cacheado).
    Por código (não um set achatado) porque cruzar com a Biblioteca
    exige nome E plataforma batendo (ver core.library.
    rom_code_for_plataforma e is_rom_backed abaixo) - nome igual em
    sistemas diferentes pode ser jogo DIFERENTE de verdade (achado
    27/08: "Celeste" comprado no Xbox e um "Celeste.gba" - quase
    certamente ROM-hack/demake amador - são jogos diferentes que só
    têm o nome igual; cruzar só por nome misturava os dois, contra o
    pedido explícito do usuário de separar por plataforma)."""
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    by_code = {}

    for code, info in cfg["systems"].items():
        by_code[code] = {covers_mod.normalize(d) for d in light_rom_display_names(code, info, roms_root)}

    heavy = heavy_mod.load_heavy_systems(cfg)
    catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
    for code in heavy:
        names = set()
        for item in catalog.get(code, []):
            stem = item["name"] if item["is_dir"] else Path(item["name"]).stem
            names.add(covers_mod.normalize(stem))
        by_code[code] = names

    return by_code


def is_rom_backed(game: dict, rom_names_by_code: dict) -> bool:
    """True quando `game` (registro da Biblioteca) é, na verdade, uma
    ROM que já mora numa aba de sistema - plataforma gravada mapeia pra
    um código ROM conhecido (`core.library.rom_code_for_plataforma`,
    nunca um fuzzy guess) E o nome bate com um item real desse mesmo
    código. Plataforma não mapeada (Steam/Xbox/GOG/etc, ou qualquer
    texto não reconhecido) nunca retorna True, mesmo que o nome
    coincida com alguma ROM de outro sistema - ver docstring de
    PLATAFORMA_ROM_CODES em core/library.py."""
    code = library_mod.rom_code_for_plataforma(game["plataforma"])
    if not code:
        return False
    return covers_mod.normalize(game["nome"]) in rom_names_by_code.get(code, set())


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config.toml não encontrado - copie config.example.toml para {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def search_cover_candidates(code: str, query: str, cfg: dict) -> list:
    """Busca por substring (não exata, não fuzzy com trava - aqui quem
    decide é o humano olhando a prévia) nas três fontes integradas.
    Usado pela tela de "capa errada, buscar outra opção".

    Ordem = prioridade: ScreenScraper primeiro (curadoria melhor,
    pedido do usuário), depois LaunchBox, libretro-thumbnails por
    último. Importa de verdade porque o resultado final é truncado em
    40 itens (results[:40]) - achado real: uma busca por título comum
    já enche as 40 vagas só com libretro-thumbnails (o índice inteiro
    do repo, substring solta acha muita coisa), o que antes fazia o
    ScreenScraper (adicionado por último) nunca aparecer."""
    systems_cfg = cfg["systems"]
    sysinfo = systems_cfg.get(code)
    if not sysinfo:
        return []
    q_norm = covers_mod.normalize(query)
    if not q_norm:
        return []
    results = []

    if code in screenscraper_mod.SYSTEM_MAP:
        try:
            ss_results = screenscraper_mod.search_game(code, query, cfg)
        except NotImplementedError:
            ss_results = []
        for r in ss_results:
            ss_id = r["id"]
            _ss_media_cache[f"{code}:{ss_id}"] = r["media_url"]
            results.append({
                "source": "screenscraper", "name": r["name"], "ss_id": ss_id,
                "preview": f"/api/cover/ss_preview?code={urllib.parse.quote(code)}&id={urllib.parse.quote(str(ss_id))}",
            })

    if code in launchbox_mod.PLATFORM_MAP:
        index = launchbox_mod.build_index()
        for norm_name, entry in index.get(code, {}).items():
            filename, orig_name = entry
            if q_norm in norm_name:
                results.append({
                    "source": "launchbox", "name": orig_name, "filename": filename,
                    "preview": launchbox_mod.IMAGE_BASE_URL + filename,
                })

    repo = sysinfo["repo"]
    base_url = f"https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/Named_Boxarts/"
    for name in covers_mod.load_tree(repo):
        if q_norm in covers_mod.normalize(name):
            results.append({
                "source": "libretro", "name": name,
                "preview": base_url + urllib.parse.quote(name + ".png"),
            })

    return results[:40]


def download_selected_cover(source: str, name: str, repo: str, filename: str, dest: Path) -> bool:
    """Baixa o candidato que o usuário escolheu na tela de busca manual
    e grava em dest (sempre .png - RetroArch só exibe thumbnail nesse
    formato). Reaproveita o fallback via API do GitHub que já existe
    pro libretro-thumbnails (cache do raw.githubusercontent.com às
    vezes serve resposta velha/truncada).

    Sempre converte via `convert`, mesmo quando a extensão declarada já
    é ".png" - achado em 02/08 que confiar na extensão (do nome do
    arquivo do LaunchBox, ou assumir que libretro-thumbnails sempre
    serve PNG de verdade) deixou capas reais da coleção com bytes JPEG
    dentro de um arquivo .png. `convert` detecta o formato pelo
    conteúdo, não pelo nome - idempotente pra um PNG de verdade."""
    src_ext = ".png"
    if source == "libretro":
        url = f"https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/Named_Boxarts/{urllib.parse.quote(name + '.png')}"
    else:
        src_ext = Path(filename).suffix or ".jpg"
        url = launchbox_mod.IMAGE_BASE_URL + filename
    tmp = dest.with_suffix(src_ext + ".tmp")

    r = subprocess.run(
        ["curl", "-sL", "--max-time", "20", "-o", str(tmp), "-w", "%{http_code}", url],
        capture_output=True, text=True,
    )
    ok = r.stdout.strip() == "200" and tmp.exists() and tmp.stat().st_size > 1000

    if not ok and source == "libretro":
        tmp.unlink(missing_ok=True)
        try:
            data = covers_mod._download_via_api(repo, name)
        except covers_mod.RateLimited:
            data = None
        if data and len(data) > 1000:
            tmp.write_bytes(data)
            ok = True

    if not ok:
        tmp.unlink(missing_ok=True)
        return False

    conv = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    return conv.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def write_settings_paths(updates: dict) -> None:
    """Atualiza só as chaves de caminho dentro de [pc]/[android] no
    config.toml, preservando o resto do arquivo (comentários, [systems],
    [cores]) intacto - regex linha a linha em vez de reescrever o TOML
    inteiro (tomllib da stdlib só lê, não escreve)."""
    text = CONFIG_PATH.read_text()
    lines = text.splitlines(keepends=True)
    section = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]")
            continue
        if section in updates:
            m = re.match(r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)"([^"]*)"(.*?)(\r?\n?)$', line)
            if m and m.group(2) in updates[section]:
                indent, key, eq, _old_val, rest, newline = m.groups()
                new_val = updates[section][key]
                lines[i] = f'{indent}{key}{eq}"{new_val}"{rest}{newline}'
    CONFIG_PATH.write_text("".join(lines))


def add_memcard_entry(console: str, label: str, path: str) -> None:
    """Adiciona uma entrada nova em [memcards.<console>] preservando o
    resto do config.toml, mesmo espírito de write_settings_paths mas
    pra chave citada ("Slot 1" = "...") em vez de chave = valor simples
    - insere logo após o cabeçalho da seção (cria a seção se ainda não
    existir, ex: usuário nunca configurou nenhum card de PS2)."""
    text = CONFIG_PATH.read_text()
    lines = text.splitlines(keepends=True)
    header = f"[memcards.{console}]"
    esc_label = label.replace("\\", "\\\\").replace('"', '\\"')
    esc_path = path.replace("\\", "\\\\").replace('"', '\\"')
    new_line = f'"{esc_label}" = "{esc_path}"\n'
    for i, line in enumerate(lines):
        if line.strip() == header:
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("["):
                j += 1
            lines.insert(j, new_line)
            CONFIG_PATH.write_text("".join(lines))
            return
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"\n{header}\n{new_line}")
    CONFIG_PATH.write_text("".join(lines))


def remove_memcard_entry(console: str, label: str) -> bool:
    """Remove a linha da entrada em [memcards.<console>] - só
    desregistra do config.toml, nunca apaga o arquivo do card (mesmo
    princípio de "nunca apaga nada sozinho" do resto do projeto)."""
    text = CONFIG_PATH.read_text()
    lines = text.splitlines(keepends=True)
    header = f"[memcards.{console}]"
    esc_label = label.replace("\\", "\\\\").replace('"', '\\"')
    key_re = re.compile(rf'^\s*"{re.escape(esc_label)}"\s*=')
    in_section = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = (stripped == header)
            continue
        if in_section and key_re.match(line):
            del lines[i]
            CONFIG_PATH.write_text("".join(lines))
            return True
    return False


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else {}


def save_registry(registry: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False))


def run_fetch_job(job_id: str, code: str, apply: bool, fallback_source: str) -> None:
    """fallback_source: "" (busca normal, libretro-thumbnails), "launchbox"
    ou "screenscraper" (segunda passada só nos no_match, um botão por
    fonte na GUI - "🔍 Buscar no LaunchBox"/"🔍 Buscar no ScreenScraper")."""
    q = _jobs[job_id]

    def emit(event: dict) -> None:
        q.put(event)

    try:
        cfg = load_config()
        capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
        systems = cfg["systems"]
        registry = load_registry()

        targets = list(systems.keys()) if code == "all" else [code]

        for sys_code in targets:
            sysinfo = systems.get(sys_code)
            if not sysinfo:
                continue

            if not fallback_source:
                def on_progress(label, status, i, total, _code=sys_code):
                    emit({"type": "progress", "code": _code, "label": label, "status": status, "i": i, "total": total})

                result = covers_mod.process_system(
                    sys_code, sysinfo["capas"], sysinfo["repo"], capas_root, registry, apply=apply,
                    on_progress=on_progress,
                )
                emit({"type": "system_done", "code": sys_code, "result": {
                    "exact": result["exact"], "fuzzy": len(result["fuzzy"]),
                    "no_match": result["no_match"], "cached": result["cached"],
                }})
            elif fallback_source == "launchbox":
                if sys_code not in launchbox_mod.PLATFORM_MAP:
                    continue
                index = launchbox_mod.build_index()

                def on_progress(label, status, i, total, _code=sys_code):
                    emit({"type": "progress", "code": _code, "label": label, "status": status, "i": i, "total": total})

                found = launchbox_mod.process_system_fallback(
                    sys_code, sysinfo["capas"], capas_root, registry, index, apply=apply, on_progress=on_progress,
                )
                emit({"type": "system_done", "code": sys_code, "result": {"found": found}})
            elif fallback_source == "screenscraper":
                if sys_code not in screenscraper_mod.SYSTEM_MAP:
                    continue

                def on_progress(label, status, i, total, _code=sys_code):
                    emit({"type": "progress", "code": _code, "label": label, "status": status, "i": i, "total": total})

                found = screenscraper_mod.process_system_fallback(
                    sys_code, sysinfo["capas"], capas_root, registry, cfg, apply=apply, on_progress=on_progress,
                )
                emit({"type": "system_done", "code": sys_code, "result": {"found": found}})

            save_registry(registry)
    except Exception as e:
        emit({"type": "error", "message": str(e)})
    finally:
        emit({"type": "job_done"})


def run_heavy_send_job(job_id: str, code: str, name: str, overwrite: bool) -> None:
    """Envia UM item de console pesado pro celular via adb - pode
    demorar (arquivos de GB), roda em thread separada. Reaproveita a
    mesma fila/stream SSE do run_fetch_job (genérica por job_id, não
    importa o tipo de job)."""
    q = _jobs[job_id]

    def emit(event: dict) -> None:
        q.put(event)

    try:
        cfg = load_config()
        heavy = heavy_mod.load_heavy_systems(cfg)
        sysinfo = heavy.get(code)
        if not sysinfo:
            emit({"type": "error", "message": f"sistema pesado desconhecido: {code}"})
            return

        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
        jogos_root = cfg["android"]["jogos_root"]
        serial = cfg["android"].get("device_serial") or None

        emit({"type": "progress", "code": code, "label": name, "status": "conectando", "i": 0, "total": 1})
        try:
            serial = adb_mod.ensure_connected(serial)
        except adb_mod.AdbError as e:
            emit({"type": "error", "message": str(e)})
            return

        emit({"type": "progress", "code": code, "label": name, "status": "enviando", "i": 0, "total": 1})
        ok, msg = heavy_mod.send_to_phone(
            code, name, roms_root, jogos_root, serial, sysinfo.get("exts", []), overwrite=overwrite,
        )
        emit({"type": "system_done", "code": code, "result": {"ok": ok, "message": msg}})
    except Exception as e:
        emit({"type": "error", "message": str(e)})
    finally:
        emit({"type": "job_done"})


def run_heavy_download_job(job_id: str, code: str, name: str) -> None:
    """Baixa UM item do Google Drive pro PC via rclone - pode demorar
    (arquivos de GB), roda em thread separada. Reaproveita a mesma
    fila/stream SSE genérica por job_id."""
    q = _jobs[job_id]

    def emit(event: dict) -> None:
        q.put(event)

    try:
        cfg = load_config()
        heavy = heavy_mod.load_heavy_systems(cfg)
        if code not in heavy:
            emit({"type": "error", "message": f"sistema pesado desconhecido: {code}"})
            return
        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()

        emit({"type": "progress", "code": code, "label": name, "status": "baixando", "i": 0, "total": 1})
        ok, msg = heavy_mod.download_from_drive(code, name, roms_root, cfg)
        emit({"type": "system_done", "code": code, "result": {"ok": ok, "message": msg}})
    except Exception as e:
        emit({"type": "error", "message": str(e)})
    finally:
        emit({"type": "job_done"})


# A partir daqui: jobs que usam o helper genérico _start_job (evento
# {"type": "log", "line": ...} - texto livre, mesmo conteúdo que a CLI
# já printava) em vez do formato progress/system_done específico de
# capas acima - operações administrativas não têm "por item" natural
# que valha a pena estruturar (backup, sync, sanitize são por lote).

def run_library_refresh_job(emit, source: str, apply: bool) -> None:
    """heroic/steam/switch via core/library.py - psn/xbox de propósito
    não entram aqui (decisão do usuário, ver docs/changelog.md 27/08).
    Mesmo princípio de sempre (nunca escreve sem apply explícito):
    calcula e mostra o merge de qualquer jeito (só em memória), só
    grava em disco se `apply`."""
    cfg = load_config()
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)

    if source == "heroic":
        owned = library_mod.read_heroic_libraries(cfg.get("heroic", {}))
        label = "Heroic (Epic+GOG+Amazon)"
    elif source == "steam":
        owned = library_mod.read_steam_library(cfg.get("steam", {}))
        label = "Steam"
    elif source == "switch":
        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
        owned = library_mod.read_switch_library(roms_root, cfg)
        label = "Nintendo Switch (roms_root/NSW/)"
        # Aproveita a varredura (que já pagou o custo do rclone) pra
        # guardar o mapa nome-limpo -> pasta real, usado pela tela de
        # decompor coletânea.
        try:
            mapa = library_mod.mapa_pastas_switch(roms_root, cfg)
            SWITCH_PASTAS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SWITCH_PASTAS_PATH.write_text(json.dumps(mapa, indent=1, ensure_ascii=False))
            emit({"type": "log", "line": f"mapa de pastas do Switch atualizado ({len(mapa)})"})
        except OSError as e:
            emit({"type": "log", "line": f"não consegui salvar o mapa de pastas: {e}"})
    else:
        emit({"type": "log", "line": f"fonte desconhecida: {source}"})
        return

    emit({"type": "log", "line": f"{label}: {len(owned)} jogo(s) possuído(s)"})
    result = library_mod.merge_owned(library, owned)
    emit({"type": "log", "line": f"novo(s): {result['added']}   já rastreado(s): {result['merged']}"})
    for a, b in result["possible_dupes"]:
        emit({"type": "log", "line": f"possível duplicata: '{a}' ~ '{b}' (não mesclado)"})

    if apply:
        library_mod.save_library(library_path, library)
        emit({"type": "log", "line": f"salvo - {len(library['games'])} jogo(s) no total"})
    else:
        emit({"type": "log", "line": "(modo simulação - nada foi salvo, marque \"aplicar\")"})


def run_library_add_job(emit, games_text: str, plataforma: str, fonte: str, apply: bool) -> None:
    cfg = load_config()
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)

    owned = [
        {"nome": line.strip(), "plataforma": plataforma, "fonte": fonte}
        for line in games_text.splitlines() if line.strip() and not line.strip().startswith("#")
    ]
    if not owned:
        emit({"type": "log", "line": "lista vazia"})
        return

    result = library_mod.merge_owned(library, owned)
    emit({"type": "log", "line": f"{len(owned)} jogo(s) na lista - novo(s): {result['added']}   "
                                  f"já rastreado(s): {result['merged']}"})
    for a, b in result["possible_dupes"]:
        emit({"type": "log", "line": f"possível duplicata: '{a}' ~ '{b}' (não mesclado)"})

    if apply:
        library_mod.save_library(library_path, library)
        emit({"type": "log", "line": f"salvo - {len(library['games'])} jogo(s) no total"})
    else:
        emit({"type": "log", "line": "(modo simulação - nada foi salvo)"})


def run_library_fetch_covers_job(emit, apply: bool) -> None:
    cfg = load_config()
    api_key = cfg.get("steamgriddb", {}).get("api_key")
    if not api_key:
        emit({"type": "log", "line": "faltando api_key em [steamgriddb] no config.toml"})
        return

    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)
    capas_dir = library_root / "capas"

    total = sum(1 for g in library["games"] if not g["capa"])
    if total == 0:
        emit({"type": "log", "line": "todo jogo já tem capa"})
        return
    emit({"type": "log", "line": f"{total} jogo(s) sem capa"})

    if not apply:
        emit({"type": "log", "line": "(modo simulação - marque \"aplicar\" pra baixar de verdade)"})
        return
    emit({"type": "log", "line": "montando índice de appid da Steam (capa oficial)..."})
    steam_appids = library_mod.steam_appid_index(cfg.get("steam", {}))
    emit({"type": "log", "line": f"{len(steam_appids)} jogo(s) da Steam com capa oficial disponível"})
    emit({"type": "log", "line": "buscando capas (Steam + SteamGridDB, pode demorar)..."})

    counter = {"i": 0}

    def on_progress(nome, status):
        counter["i"] += 1
        emit({"type": "progress", "code": "biblioteca", "label": nome, "status": status,
              "i": counter["i"], "total": total})
        if counter["i"] % 20 == 0:
            library_mod.save_library(library_path, library)

    result = library_mod.fetch_covers(library, capas_dir, api_key, on_progress=on_progress,
                                      steam_appids=steam_appids, cfg=cfg)
    library_mod.save_library(library_path, library)
    emit({"type": "log", "line": f"baixado(s): {result['baixado']} ({result['via_steam']} Steam, {result['via_ss']} ScreenScraper)   "
                                  f"sem_match: {result['sem_match']}   erro: {result['erro']}"})


def run_heavy_fetch_covers_job(emit, code: str, apply: bool) -> None:
    """Capa pra ROM pesada usando TODAS as fontes do projeto, em
    cascata - cada passada só tenta o que a anterior não resolveu
    (pedido do usuário 28/08: "e as outras fontes que usamos, não é
    melhor? faz ele procurar em todas"). Ordem = qualidade de
    curadoria, do melhor pro mais genérico:
    1. libretro-thumbnails (`covers.process_system_cloud`) - mesma
       lógica/match do `fetch-covers-cloud` da CLI, só que lendo a
       lista de jogos do catálogo CACHEADO em vez de chamar rclone ao
       vivo (~90s por sistema, inviável num botão). Pulado no PS1, que
       está em COVERS_EXCLUDED (repo grande demais pra API do GitHub).
    2. ScreenScraper - a fonte de melhor curadoria segundo o usuário
       (ver ordem em search_cover_candidates). Passou a cobrir os
       sistemas pesados em 28/08 (ids conferidos contra a API real,
       ver SYSTEM_MAP).
    3. LaunchBox - idem, cobertura nova pros pesados (PLATFORM_MAP).
    4. SteamGridDB pro que ainda sobrou - o mais genérico, mas o único
       que pega jogo obscuro/fan-art.
    As passadas 2 e 3 reaproveitam `process_system_fallback` dos
    módulos, que já lê o registry pra saber quem ficou sem match."""
    cfg = load_config()
    heavy = heavy_mod.load_heavy_systems(cfg)
    sysinfo = heavy.get(code)
    if not sysinfo:
        emit({"type": "log", "line": f"sistema pesado desconhecido: {code}"})
        return

    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    capas_dir = capas_root / sysinfo["capas"] / "Named_Boxarts"
    catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
    items = catalog.get(code, [])
    if not items:
        emit({"type": "log", "line": f"catálogo de {code} vazio - rode \"🔄 Atualizar catálogo\" antes"})
        return
    labels = sorted({(i["name"] if i["is_dir"] else Path(i["name"]).stem) for i in items})
    emit({"type": "log", "line": f"{len(labels)} jogo(s) no catálogo de {code}"})

    faltando = [lb for lb in labels if not any((capas_dir / f"{lb}{e}").is_file() for e in (".png", ".jpg"))]
    emit({"type": "log", "line": f"{len(faltando)} sem capa ainda"})
    if not faltando:
        return
    if not apply:
        emit({"type": "log", "line": "(modo simulação - marque \"aplicar\" pra baixar de verdade)"})
        return

    def ainda_sem_capa():
        return [lb for lb in faltando
                if not any((capas_dir / f"{lb}{e}").is_file() for e in (".png", ".jpg"))]

    registry = load_registry()
    if code not in COVERS_EXCLUDED:
        emit({"type": "log", "line": "1/4 libretro-thumbnails..."})
        result = covers_mod.process_system_cloud(
            code, sysinfo["capas"], sysinfo["repo"], capas_root, faltando, registry, apply=True,
        )
        save_registry(registry)
        emit({"type": "log", "line": f"  exato: {result['exact']}   fuzzy (não aplicado): {len(result['fuzzy'])}   "
                                      f"sem_match: {result['no_match']}"})
    else:
        emit({"type": "log", "line": f"1/4 libretro-thumbnails pulado ({code} está em COVERS_EXCLUDED)"})

    # ScreenScraper e LaunchBox trabalham em cima do registry (só
    # reprocessam quem ficou "no_match"), então quem nunca passou pelo
    # libretro (PS1) precisa ser marcado antes, senão as duas não têm o
    # que reprocessar.
    reg_sys = registry.setdefault(code, {})
    for label in ainda_sem_capa():
        if label not in reg_sys:
            reg_sys[label] = {"status": "no_match"}
    save_registry(registry)

    for passo, (nome_fonte, mod, suportado) in enumerate([
        ("ScreenScraper", screenscraper_mod, code in screenscraper_mod.SYSTEM_MAP),
        ("LaunchBox", launchbox_mod, code in launchbox_mod.PLATFORM_MAP),
    ], start=2):
        restam = len(ainda_sem_capa())
        if not restam:
            break
        if not suportado:
            emit({"type": "log", "line": f"{passo}/4 {nome_fonte} pulado ({code} não mapeado)"})
            continue
        emit({"type": "log", "line": f"{passo}/4 {nome_fonte} pros {restam} restantes..."})
        try:
            if mod is screenscraper_mod:
                achou = mod.process_system_fallback(
                    code, sysinfo["capas"], capas_root, registry, cfg, apply=True)
            else:
                achou = mod.process_system_fallback(
                    code, sysinfo["capas"], capas_root, registry, mod.build_index(), apply=True)
            save_registry(registry)
            emit({"type": "log", "line": f"  achou: {achou}"})
        except Exception as e:
            emit({"type": "log", "line": f"  {nome_fonte} falhou: {type(e).__name__}: {str(e)[:120]}"})

    api_key = cfg.get("steamgriddb", {}).get("api_key")
    if not api_key:
        emit({"type": "log", "line": "4/4 SteamGridDB pulado (faltando api_key em [steamgriddb])"})
        return

    ainda_faltando = ainda_sem_capa()
    emit({"type": "log", "line": f"4/4 SteamGridDB pros {len(ainda_faltando)} restantes..."})
    baixado = sem_match = erro = 0
    for i, label in enumerate(ainda_faltando, 1):
        try:
            url = library_mod.find_cover_steamgriddb(label, api_key)
        except Exception:
            erro += 1
            continue
        if not url:
            sem_match += 1
            emit({"type": "progress", "code": code, "label": label, "status": "sem_match",
                  "i": i, "total": len(ainda_faltando)})
            continue
        capas_dir.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": library_mod._BROWSER_USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
        except Exception:
            erro += 1
            continue
        # Mesmo cuidado do upload manual: grava num temporário e só
        # converte pro .png final (o formato que o RetroArch exibe).
        tmp = capas_dir / f"{label}.sgdb.tmp"
        tmp.write_bytes(data)
        conv = subprocess.run(["convert", str(tmp), str(capas_dir / f"{label}.png")],
                              capture_output=True, text=True)
        tmp.unlink(missing_ok=True)
        if conv.returncode == 0:
            baixado += 1
            registry.setdefault(code, {})[label] = {"status": "manual", "source": "steamgriddb"}
            emit({"type": "progress", "code": code, "label": label, "status": "baixado",
                  "i": i, "total": len(ainda_faltando)})
        else:
            erro += 1
    save_registry(registry)
    emit({"type": "log", "line": f"  baixado: {baixado}   sem_match: {sem_match}   erro: {erro}"})


def run_heavy_catalog_job(emit) -> None:
    cfg = load_config()
    emit({"type": "log", "line": "consultando o Google Drive (pode demorar - ~90s por sistema)..."})
    catalog = sortear_mod.refresh_heavy_catalog(cfg)
    for code, names in catalog.items():
        emit({"type": "log", "line": f"{code}: {len(names)} jogo(s)"})
    sortear_mod.save_heavy_catalog(HEAVY_CATALOG_PATH, catalog)
    total = sum(len(n) for n in catalog.values())
    emit({"type": "log", "line": f"catálogo salvo - {total} jogo(s) no total"})


def run_backup_config_job(emit, target: str, apply: bool) -> None:
    cfg = load_config()
    backups_root = Path(cfg["pc"]["backups_root"]).expanduser()
    targets = ["pc", "android"] if target == "all" else [target]

    if "pc" in targets:
        plan = config_backup_mod.backup_pc(cfg, backups_root, apply=apply)
        emit({"type": "log", "line": f"[PC] -> {plan['dest']}"})
        if apply:
            for k, v in plan["counts"].items():
                emit({"type": "log", "line": f"  {k}: {v} arquivo(s) copiado(s)"})

    if "android" in targets:
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            emit({"type": "log", "line": f"[Android] erro de adb: {e}"})
            serial = None
        if serial:
            plan = config_backup_mod.backup_android(cfg, backups_root, serial, apply=apply)
            emit({"type": "log", "line": f"[Android] -> {plan['dest']}"})
            if apply:
                for k, v in plan["counts"].items():
                    ok = plan["ok"][k]
                    emit({"type": "log", "line": f"  {k}: {v} arquivo(s)" + ("" if ok else "  FALHOU")})

    if not apply:
        emit({"type": "log", "line": "(modo simulação - nada foi copiado)"})


def run_backup_saves_job(emit, apply: bool) -> None:
    cfg = load_config()
    items = pc_backup_mod.plan(cfg)
    if not items:
        emit({"type": "log", "line": "nada pra fazer backup (tudo já copiado, ou dolphin_data_root vazio)"})
        return
    for item in items:
        emit({"type": "log", "line": f"[{item['action']}] {item['rel_path']}"})
    if apply:
        pc_backup_mod.apply(items)
        emit({"type": "log", "line": f"copiado: {len(items)} arquivo(s)"})
    else:
        emit({"type": "log", "line": f"total: {len(items)} arquivo(s) (modo simulação)"})


def run_sanitize_names_job(emit, target: str, apply: bool) -> None:
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    roots = []
    if target in ("all", "capas"):
        roots.append(("Capas", capas_root))
    if target in ("all", "roms"):
        roots.append(("ROMs", roms_root))

    for label, root in roots:
        results = sanitize_mod.scan_and_rename(root, apply=apply)
        if not results:
            emit({"type": "log", "line": f"{label}: nada pra renomear"})
            continue
        for r in results:
            old_name, new_name = Path(r["old"]).name, Path(r["new"]).name
            emit({"type": "log", "line": f"[{label}] {r['status']}: {old_name} -> {new_name}"})

    if not apply:
        emit({"type": "log", "line": "(modo simulação - nada foi renomeado)"})


def run_rebuild_playlist_job(emit, code: str, target: str, apply: bool) -> None:
    cfg = load_config()
    sysinfo = cfg["systems"].get(code)
    if not sysinfo:
        emit({"type": "log", "line": f"sistema desconhecido em [systems]: '{code}'"})
        return
    db_name = f"{sysinfo['capas']}.lpl"
    exts = sysinfo.get("exts", [])
    targets = ["pc", "android"] if target == "all" else [target]

    if "pc" in targets:
        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
        content_dir = roms_root / code
        dest = Path(cfg["pc"]["retroarch_root"]).expanduser() / "playlists" / db_name
        names = playlist_mod.list_local_names(code, roms_root, exts)
        emit({"type": "log", "line": f"[PC] {len(names)} jogo(s) em {content_dir}"})
        if apply and names:
            items = [(str(content_dir / n), Path(n).stem) for n in names]
            pl = playlist_mod.make_playlist(items, str(content_dir), exts, db_name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(pl, indent=1, ensure_ascii=False))
            emit({"type": "log", "line": f"[PC] gravado em {dest}"})

    if "android" in targets:
        jogos_root = cfg["android"]["jogos_root"]
        remote_content_dir = f"{jogos_root.rstrip('/')}/{code}"
        remote_dest = f"{cfg['android']['retroarch_root'].rstrip('/')}/playlists/{db_name}"
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            emit({"type": "log", "line": f"[Android] erro de adb: {e}"})
            return
        names = playlist_mod.list_remote_names(code, jogos_root, exts, serial)
        emit({"type": "log", "line": f"[Android] {len(names)} jogo(s) em {remote_content_dir}"})
        if apply and names:
            items = [(f"{remote_content_dir}/{n}", Path(n).stem) for n in names]
            pl = playlist_mod.make_playlist(items, remote_content_dir, exts, db_name)
            tmp_dir = ROOT / "cache" / "playlists_tmp"
            ok = playlist_mod.push_playlist(pl, remote_dest, serial, tmp_dir)
            emit({"type": "log", "line": f"[Android] {'enviado' if ok else 'FALHOU'}"})

    if not apply:
        emit({"type": "log", "line": "(modo simulação - nada foi escrito)"})


def run_emu_sync_job(emit, source: str, apply: bool) -> None:
    cfg = load_config()
    sources = list(emu_sync_mod.SOURCES) if source == "all" else [source]
    local_mode = emu_sync_mod.running_in_termux()
    serial = None
    if not local_mode:
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            emit({"type": "log", "line": f"erro de adb: {e}"})
            return

    all_actions, all_conflicts = [], []
    for src in sources:
        result = emu_sync_mod.plan(src, cfg, serial=serial, local_mode=local_mode)
        all_actions += result["actions"]
        all_conflicts += result["conflicts"]

    if not all_actions and not all_conflicts:
        emit({"type": "log", "line": "nada pra sincronizar (tudo já igual nas três pontas)"})
        return
    for a in all_actions:
        emit({"type": "log", "line": f"[{a['source']}] {a['direction']}: {a['rel_path']}"})
    for c in all_conflicts:
        emit({"type": "log", "line": f"CONFLITO [{c['source']}] {c['rel_path']} "
                                      f"(pc={c['pc_mtime']}, android={c['android_mtime']})"})

    if apply:
        results = emu_sync_mod.apply(all_actions, cfg, serial=serial, local_mode=local_mode)
        erros = [r for r in results if not r["ok"]]
        emit({"type": "log", "line": f"aplicado: {len(results) - len(erros)}/{len(results)}"})
        for r in erros:
            emit({"type": "log", "line": f"erro: {r['source']}/{r['rel_path']}: {r['erro']}"})
    else:
        emit({"type": "log", "line": f"total: {len(all_actions)} ação(ões) (modo simulação)"})


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silencioso - o terminal já mostra o suficiente sem isso

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _cover_path(self, code: str, label: str):
        """Resolve o caminho da capa (código do sistema + label) e o
        diretório Named_Boxarts dela - leve OU pesado (pedido do
        usuário 27/08: upload/renomear/apagar capa manual também pra
        ROMs pesadas, não só leve). Retorna (None, None) se o sistema
        não existir em nenhum dos dois, não tiver "capas" configurado,
        OU se o label não puder virar nome de arquivo com segurança -
        este é o funil por onde passam todos os endpoints que escrevem
        capa, então validar aqui cobre todos de uma vez (ver
        nome_de_arquivo_seguro)."""
        if not nome_de_arquivo_seguro(label or ""):
            return None, None
        cfg = load_config()
        info = cfg["systems"].get(code) or heavy_mod.load_heavy_systems(cfg).get(code)
        if not info or not info.get("capas"):
            return None, None
        capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
        capas_dir = capas_root / info["capas"] / "Named_Boxarts"
        return capas_dir, info

    def _memcard_path(self, key: str):
        """Resolve uma "key" tipo "ps1:Slot 1" pro (caminho do arquivo,
        console em maiúsculo) configurados em config.toml [memcards].
        Retorna (None, None) se a key não bater com nenhum card."""
        console, _, label = key.partition(":")
        cfg = load_config()
        path = cfg.get("memcards", {}).get(console, {}).get(label)
        if not path:
            return None, None
        return Path(path).expanduser(), console.upper()

    def _file(self, path: Path, content_type: str, no_cache: bool = False):
        if not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if no_cache:
            # app.js/index.html mudam com frequência durante o
            # desenvolvimento (sem Last-Modified/ETag o navegador é
            # livre pra usar cache heurístico) - sem isso, um F5 normal
            # pode continuar servindo JS velho do disk cache e uma
            # correção parece "não ter feito efeito" até um hard
            # refresh. Não se aplica a /images (capas já usam
            # cache-bust por query param, ver buildCoverCard).
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _responder_erro(self, e: Exception) -> None:
        """Qualquer exceção não prevista vira 500 com mensagem, em vez
        de derrubar a conexão sem resposta nenhuma - achado 28/08 numa
        auditoria: um label inválido levantava FileNotFoundError e o
        cliente só via "conexão fechada", sem pista do que houve (no
        celular, isso aparecia como "bugou"). O traceback vai pro
        terminal, que é onde o dono do servidor consegue ler."""
        traceback.print_exc()
        try:
            self._json({"error": f"erro interno: {type(e).__name__}: {e}"}, 500)
        except Exception:
            pass  # conexão já morreu do outro lado; nada a fazer

    def do_GET(self):
        try:
            return self._do_GET()
        except Exception as e:
            return self._responder_erro(e)

    def _do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8", no_cache=True)

        if parts == ["tests", "test_app.html"]:
            # Página de teste do JS (ver tests/test_app.html) - servida
            # pelo próprio servidor porque ela carrega /static/logic.js,
            # e abrir por file:// esbarraria na política de origem.
            return self._file(ROOT / "tests" / "test_app.html",
                              "text/html; charset=utf-8", no_cache=True)

        if parts[:1] == ["static"] and len(parts) == 2:
            ext = parts[1].rsplit(".", 1)[-1]
            ctype = {"js": "application/javascript", "css": "text/css"}.get(ext, "application/octet-stream")
            return self._file(STATIC_DIR / parts[1], ctype, no_cache=True)

        if parts[:2] == ["api", "systems"]:
            cfg = load_config()
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            registry = load_registry()
            out = []
            for code, info in cfg["systems"].items():
                if code in COVERS_EXCLUDED:
                    continue
                capas_dir = capas_root / info["capas"] / "Named_Boxarts"
                count = len(list(capas_dir.glob("*.png"))) + len(list(capas_dir.glob("*.jpg"))) if capas_dir.is_dir() else 0
                no_match = sum(1 for v in registry.get(code, {}).values() if v.get("status") == "no_match")
                missing = len(covers_mod.missing_cover_labels(roms_root, code, info.get("exts", []), capas_dir))
                out.append({
                    "code": code, "capas": info["capas"], "count": count,
                    "no_match": no_match, "missing": missing, "has_launchbox": code in launchbox_mod.PLATFORM_MAP,
                    "has_screenscraper": code in screenscraper_mod.SYSTEM_MAP,
                })
            return self._json(out)

        if parts == ["api", "search_library"]:
            # Busca geral - pedido do usuário pra achar um jogo sem
            # precisar já saber em qual sistema/aba ele está, e depois
            # (27/08) unificada pra cobrir TUDO (leve + pesada +
            # Biblioteca) num só lugar - antes só leve tinha essa busca,
            # Biblioteca tinha a própria (removida do #library-controls,
            # ver index.html). Substring simples (case/acento-
            # insensitive), não a normalização "agressiva" de
            # covers.normalize (que tira tag/artigo/parênteses - certa
            # pra decidir se dois resultados são o mesmo jogo, errada pra
            # busca livre onde o usuário pode digitar exatamente uma tag
            # tipo "usa"). code_filter (leve, do <select> ao lado da
            # busca) só faz sentido restrito a "leve" - com ele marcado,
            # pesada/Biblioteca não entram no resultado.
            q = query.get("q", [""])[0].strip()
            code_filter = query.get("code", [""])[0]
            if len(q) < 2:
                return self._json([])
            q_norm = unicodedata.normalize("NFKD", q).encode("ascii", "ignore").decode().lower()
            cfg = load_config()
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            out = []
            for code, info in cfg["systems"].items():
                if code in COVERS_EXCLUDED:
                    continue
                if code_filter and code_filter != code:
                    continue
                capas_dir = capas_root / info["capas"] / "Named_Boxarts"
                if not capas_dir.is_dir():
                    continue
                romname_dat = arcade_romname_dat(code)
                for p in capas_dir.iterdir():
                    if p.suffix.lower() not in (".png", ".jpg"):
                        continue
                    label = p.stem
                    display_name = covers_mod.arcade_display_name(label, romname_dat) if romname_dat else None
                    # Arcade: também bate pelo nome de exibição (ex:
                    # "metal slug" acha "mslug2") - sem isso a busca só
                    # funcionaria digitando o código curto do romset.
                    haystack = label + (" " + display_name if display_name else "")
                    haystack_norm = unicodedata.normalize("NFKD", haystack).encode("ascii", "ignore").decode().lower()
                    if q_norm in haystack_norm:
                        out.append({"kind": "leve", "code": code, "label": label, "file": p.name, "display_name": display_name})

            if not code_filter:
                heavy = heavy_mod.load_heavy_systems(cfg)
                catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
                for code, items in catalog.items():
                    sysinfo = heavy.get(code, {})
                    for item in items:
                        haystack_norm = unicodedata.normalize("NFKD", item["name"]).encode("ascii", "ignore").decode().lower()
                        if q_norm in haystack_norm:
                            out.append({"kind": "pesado", "code": code, "label": item["name"],
                                        "display_name": None, "system_label": sysinfo.get("nome", code)})

                library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
                library = library_mod.load_library(library_path)
                rom_names_by_code = rom_normalized_names_by_code(cfg)
                for g in library["games"]:
                    if is_rom_backed(g, rom_names_by_code):
                        continue  # já mora numa aba de ROM - ver GET /api/library
                    haystack_norm = unicodedata.normalize("NFKD", g["nome"]).encode("ascii", "ignore").decode().lower()
                    if q_norm in haystack_norm:
                        out.append({"kind": "biblioteca", "code": None, "label": g["id"],
                                    "display_name": g["nome"], "fontes": g["fontes"],
                                    "plataforma": g["plataforma"]})

            out.sort(key=lambda x: (x["display_name"] or x["label"]).lower())
            return self._json(out[:100])

        if parts[:2] == ["api", "covers"] and len(parts) == 3:
            code = parts[2]
            cfg = load_config()
            info = cfg["systems"].get(code)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            capas_dir = capas_root / info["capas"] / "Named_Boxarts"
            registry = load_registry()
            reg_sys = registry.get(code, {})
            files = sorted(p.name for p in capas_dir.iterdir() if p.suffix.lower() in (".png", ".jpg")) if capas_dir.is_dir() else []
            # saves_root/states_root não têm subpasta por sistema (achatado,
            # ver core/rom_rename.py) - lista cada pasta UMA vez e faz busca
            # por prefixo via bisect, em vez de escanear a pasta inteira pra
            # cada capa (isso escalaria mal com centenas de capas).
            saves_dir = Path(cfg["pc"]["saves_root"]).expanduser()
            states_dir = Path(cfg["pc"]["states_root"]).expanduser()
            saves_names = sorted(p.name for p in saves_dir.iterdir() if p.is_file()) if saves_dir.is_dir() else []
            states_names = sorted(p.name for p in states_dir.iterdir() if p.is_file()) if states_dir.is_dir() else []

            def has_flat_match(sorted_names: list, label: str) -> bool:
                prefix = label + "."
                i = bisect.bisect_left(sorted_names, prefix)
                return i < len(sorted_names) and sorted_names[i].startswith(prefix)

            # Arcade: o arquivo/label é o nome curto do romset (ex:
            # "mslug2") - display_name é só pra GUI mostrar "Metal Slug
            # 2" na tela, nunca usado pra rename/apagar (esses sempre
            # operam no label curto de verdade, ver core/rom_rename.py).
            romname_dat = arcade_romname_dat(code)

            # Cruza com a Biblioteca (nome normalizado igual ao
            # matching de capa - tags de região/artigo não devem
            # impedir "Sonic the Hedgehog (USA)" de achar "Sonic the
            # Hedgehog" na planilha - E plataforma mapeando pra este
            # `code`, ver find_for_rom/PLATAFORMA_ROM_CODES; nome igual
            # sozinho não basta, achado 27/08 sobre Celeste Xbox vs
            # Celeste GBA) pra mostrar iniciado/finalizado/platinado/
            # nota direto na galeria - só leitura, não decide nada
            # sozinho.
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            lib_by_norm = library_mod.index_by_rom_name(library_mod.load_library(library_path))

            def biblioteca_info(shown_name: str):
                g = library_mod.find_for_rom(lib_by_norm, shown_name, code)
                if not g:
                    return None
                return {"iniciado": g["iniciado"], "finalizado": g["finalizado"],
                        "platinado": g["platinado"], "nota": g["nota"]}

            out = []
            for f in files:
                label = Path(f).stem
                status = reg_sys.get(label, {}).get("status")
                display_name = covers_mod.arcade_display_name(label, romname_dat) if romname_dat else None
                out.append({
                "file": f, "label": label, "status": status,
                "flagged": status == "flagged_wrong", "duplicated": status == "duplicate",
                "has_save": has_flat_match(saves_names, label), "has_state": has_flat_match(states_names, label),
                "display_name": display_name,
                "biblioteca": biblioteca_info(display_name or label),
            })

            # ROMs já organizadas mas sem capa nenhuma ainda (nem
            # tentativa registrada) - sem isso ficam invisíveis pra
            # sempre, já que a busca em massa só revê capas que já
            # existem (ver core/covers.py missing_cover_labels).
            if code not in covers_mod.COVERS_EXCLUDED:
                roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
                for label in covers_mod.missing_cover_labels(roms_root, code, info.get("exts", []), capas_dir):
                    display_name = covers_mod.arcade_display_name(label, romname_dat) if romname_dat else None
                    out.append({
                        "file": None, "label": label, "status": "no_cover",
                        "flagged": False, "duplicated": False,
                        "has_save": has_flat_match(saves_names, label), "has_state": has_flat_match(states_names, label),
                        "display_name": display_name,
                        "biblioteca": biblioteca_info(display_name or label),
                    })

            out.sort(key=lambda item: (item["display_name"] or item["label"]).lower())
            return self._json(out)

        if parts[:1] == ["images"] and len(parts) >= 3:
            code = parts[1]
            filename = urllib.parse.unquote("/".join(parts[2:]))
            cfg = load_config()
            info = cfg["systems"].get(code) or heavy_mod.load_heavy_systems(cfg).get(code)
            if not info or not info.get("capas"):
                return self._file(Path("/nonexistent"), "image/png")
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            path = capas_root / info["capas"] / "Named_Boxarts" / filename
            ctype = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            return self._file(path, ctype)

        if parts[:1] == ["library-images"] and len(parts) >= 2:
            # g.capa em library.json já guarda o caminho relativo
            # ("capas/<id>.png") - serve direto a partir daí, mesmo
            # padrão do /images/<code>/<arquivo> das ROMs.
            rel_path = urllib.parse.unquote("/".join(parts[1:]))
            cfg = load_config()
            library_root = Path(cfg["pc"]["library_root"]).expanduser().resolve()
            path = (library_root / rel_path).resolve()
            if library_root not in path.parents:
                return self._file(Path("/nonexistent"), "image/png")
            return self._file(path, "image/png")

        if parts == ["api", "settings"]:
            cfg = load_config()
            return self._json({"pc": cfg.get("pc", {}), "android": cfg.get("android", {})})

        if parts == ["api", "emu_sync", "sources"]:
            return self._json([{"code": k, "nome": v["nome"]} for k, v in emu_sync_mod.SOURCES.items()])

        if parts == ["api", "sortear", "systems"]:
            # Lista pra popular o <select> - leve (sempre local), pesado
            # (do catálogo cacheado, mesmo que a CLI usa) e os 3 grupos
            # (leve/pesado/biblioteca inteiros, pedido do usuário
            # 31/08 - "permitir sorteio por grupos"). "(leve)"/"(pesado)"
            # não vai mais no label de cada sistema individual - o
            # `kind` continua no JSON pra quem quiser, só não aparece
            # mais concatenado no texto do rótulo.
            cfg = load_config()
            out = [{"code": c, "label": info["capas"], "kind": "leve"} for c, info in cfg["systems"].items()]
            for c, info in heavy_mod.load_heavy_systems(cfg).items():
                out.append({"code": c, "label": info.get("nome", c), "kind": "pesado"})
            out.sort(key=lambda x: x["label"])
            grupos = [{"code": "leve", "label": "🕹 ROMs leves (todas)", "kind": "grupo"},
                      {"code": "pesado", "label": "📦 ROMs pesadas (todas)", "kind": "grupo"},
                      {"code": "biblioteca", "label": "📚 Biblioteca (toda)", "kind": "grupo"}]
            return self._json({"grupos": grupos, "sistemas": out})

        if parts == ["api", "sortear"]:
            cfg = load_config()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
            system = query.get("system", [""])[0].strip() or None

            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            rom_names_by_code = rom_normalized_names_by_code(cfg)

            try:
                pool = sortear_mod.build_pool(cfg, roms_root, catalog, system,
                                              library=library, rom_names_by_code=rom_names_by_code)
            except ValueError:
                return self._json({"error": f"sistema desconhecido: '{system}'"}, 400)
            if not pool:
                return self._json({"error": "nenhum jogo encontrado pra sortear"}, 404)

            code, nome, kind = sortear_mod.draw(pool)
            heavy = heavy_mod.load_heavy_systems(cfg)
            if kind == "biblioteca":
                label = "Biblioteca"
            else:
                sysinfo = cfg["systems"][code] if kind == "leve" else heavy[code]
                label = sysinfo["capas"] if kind == "leve" else sysinfo.get("nome", code)
            resp = {"nome": nome, "codigo": code, "label": label, "kind": kind, "pool_size": len(pool)}

            if kind == "biblioteca":
                # Capa/progresso do jogo de Biblioteca sorteado - mesma
                # resolução que /api/ranking e /api/iniciados já fazem.
                jogo = next((g for g in library["games"] if g["nome"] == nome), None)
                if jogo and jogo.get("capa"):
                    resp["capa"] = com_versao(f"/library-images/{urllib.parse.quote(jogo['capa'])}",
                                              Path(cfg["pc"]["library_root"]).expanduser() / jogo["capa"])
                return self._json(resp)

            # Capa: mesmo nome (sem extensão de ROM) que o resto do
            # projeto já usa - só existe pra sistema com "capas"
            # configurado (todo leve; pesado só os 5 com fetch-covers-
            # cloud rodado, PS1 fica sem por decisão de sempre).
            if sysinfo.get("capas"):
                capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
                capas_dir = capas_root / sysinfo["capas"] / "Named_Boxarts"
                stem = Path(nome).stem
                for ext in (".png", ".jpg"):
                    if (capas_dir / f"{stem}{ext}").is_file():
                        resp["capa"] = f"/images/{code}/{urllib.parse.quote(stem + ext)}"
                        break

            if kind == "pesado":
                local_names = {i["name"] for i in heavy_mod.list_local(code, roms_root, sysinfo.get("exts", []))}
                resp["local"] = nome in local_names

            return self._json(resp)

        if parts == ["api", "library"]:
            # library_root já é a mesma pasta sincronizada pelo Google
            # Drive que ROMs/Capas, então isso funciona igual rodando em
            # modo Android (Termux) - nunca gera o arquivo sozinho, só lê
            # o que já existe. Cadastro de fonte nova (loja) continua via
            # CLI (library-import-sheet/library-refresh/library-add);
            # tracking (nota/iniciado/etc) é editável na tela pra
            # qualquer jogo, ver /api/library/update e /api/library/track.
            #
            # Exclui jogo que na verdade é ROM (nome E plataforma
            # batendo com uma ROM leve local ou do catálogo pesado
            # cacheado, ver is_rom_backed/PLATAFORMA_ROM_CODES - nome
            # igual sozinho NÃO basta, ver achado 27/08 sobre Celeste
            # Xbox vs Celeste GBA) - pedido do usuário 27/08: "na
            # biblioteca ainda tem jogos das ROMs, mudar os dados desses
            # jogos para lá". O dado nunca é apagado (continua no
            # library.json), só some da listagem aqui porque agora
            # "mora" na aba do sistema correspondente (ver
            # biblioteca_info em /api/covers e /api/heavy/roms).
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            rom_names_by_code = rom_normalized_names_by_code(cfg)
            games = [g for g in library["games"] if not is_rom_backed(g, rom_names_by_code)]
            # capa_url já vem pronta e versionada (ver com_versao) - o
            # cliente não monta mais a URL na mão, senão perderia o
            # cache-bust e a troca de capa não apareceria.
            library_root = Path(cfg["pc"]["library_root"]).expanduser()
            out = []
            for g in games:
                capa_url = None
                if g["capa"]:
                    capa_url = com_versao(f"/library-images/{urllib.parse.quote(g['capa'])}",
                                          library_root / g["capa"])
                out.append({**g, "capa_url": capa_url})
            return self._json(out)

        if parts in (["api", "ranking"], ["api", "iniciados"]):
            # Duas visões que cruzam TODA a coleção de uma vez (pedido
            # do usuário 28/08: botões próprios ao lado de Sortear) -
            # ROM leve, pesada e Biblioteca juntas, porque desde o
            # tracking universal (27/08) o library.json é a fonte única
            # de progresso pra qualquer tipo de jogo. Diferente da aba
            # Biblioteca, aqui NÃO exclui o que é ROM: o objetivo é
            # justamente ver tudo junto. Jogo oculto fica de fora.
            #
            # `ranking`: quem tem nota, maior primeiro.
            # `iniciados`: começou e ainda não terminou (o que está "em
            # andamento" de verdade) - sem nota não desempata nada, então
            # ordena por nome.
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            visiveis = [g for g in library["games"] if not g.get("oculto")]

            if parts[1] == "ranking":
                sel = [g for g in visiveis if g["nota"] is not None]
                sel.sort(key=lambda g: (-g["nota"], g["nome"].lower()))
            else:
                sel = [g for g in visiveis if g["iniciado"] and not g["finalizado"]]
                sel.sort(key=lambda g: g["nome"].lower())

            # Capa: jogo que é ROM tem a capa na pasta do sistema, não
            # em library_root/capas - resolve os dois casos aqui pra
            # tela não precisar saber a diferença.
            rom_names_by_code = rom_normalized_names_by_code(cfg)
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            heavy = heavy_mod.load_heavy_systems(cfg)
            out = []
            for g in sel:
                capa = None
                if g["capa"]:
                    capa = com_versao(f"/library-images/{urllib.parse.quote(g['capa'])}",
                                      Path(cfg["pc"]["library_root"]).expanduser() / g["capa"])
                code = library_mod.rom_code_for_plataforma(g["plataforma"])
                if not capa and code and covers_mod.normalize(g["nome"]) in rom_names_by_code.get(code, set()):
                    info = cfg["systems"].get(code) or heavy.get(code)
                    if info and info.get("capas"):
                        capas_dir = capas_root / info["capas"] / "Named_Boxarts"
                        for ext in (".png", ".jpg"):
                            if (capas_dir / f"{g['nome']}{ext}").is_file():
                                capa = com_versao(f"/images/{code}/{urllib.parse.quote(g['nome'] + ext)}",
                                                  capas_dir / f"{g['nome']}{ext}")
                                break
                out.append({**g, "capa_url": capa})
            return self._json(out)

        if parts == ["api", "estatisticas"]:
            # Visão agregada da coleção inteira - pedido do usuário
            # 31/08 ("estatísticas que mostram jogos zerados, platinados
            # e tempo de jogo total"). Mesma base do Ranking/Iniciados:
            # todo jogo com progresso mora no library.json, oculto fica
            # de fora. `tempo_total_horas` sai cru pro front formatar
            # (anos/meses/dias/horas é decisão de exibição, mora em
            # logic.js - mesmo padrão de notaColor/notaTexto).
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            visiveis = [g for g in library["games"] if not g.get("oculto")]
            com_nota = [g["nota"] for g in visiveis if g["nota"] is not None]

            return self._json({
                "total": len(visiveis),
                "zerados": sum(1 for g in visiveis if g["finalizado"]),
                "platinados": sum(1 for g in visiveis if g["platinado"]),
                "jogando": sum(1 for g in visiveis if g["iniciado"] and not g["finalizado"]),
                "com_nota": len(com_nota),
                "nota_media": round(sum(com_nota) / len(com_nota), 2) if com_nota else None,
                "tempo_total_horas": round(sum(library_mod.tempo_para_horas(g["tempo"]) for g in visiveis), 2),
                "com_genero": sum(1 for g in visiveis if g.get("genero")),
            })

        if parts == ["api", "switch", "colecao"]:
            # Sugestão de quais jogos uma coletânea contém, lendo o que
            # existe DENTRO da pasta (ver core/library.
            # nomes_dentro_da_colecao). É chute pra pré-preencher a tela
            # de decompor - quem decide é o usuário.
            nome = query.get("nome", [""])[0].strip()
            if not nome:
                return self._json({"error": "nome obrigatório"}, 400)
            cfg = load_config()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            mapa = {}
            if SWITCH_PASTAS_PATH.exists():
                mapa = json.loads(SWITCH_PASTAS_PATH.read_text())
            pasta_real = mapa.get(nome)
            if not pasta_real:
                # Sem cache ainda (ou pasta nova): tenta só o lado local,
                # que é barato. O Drive fica pro próximo "🔄 Switch".
                pasta_real = library_mod.mapa_pastas_switch(roms_root, None).get(nome)
            if not pasta_real:
                return self._json({"pasta": None, "sugestoes": [],
                                   "aviso": "não achei a pasta desse jogo - rode \"🔄 Switch\" "
                                            "pra atualizar o mapa, ou digite os nomes na mão"})
            itens = library_mod.conteudo_da_pasta_switch(pasta_real, roms_root, cfg)
            return self._json({"pasta": pasta_real,
                               "sugestoes": library_mod.nomes_dentro_da_colecao(itens)})

        if parts == ["api", "cover", "search"]:
            code = query.get("code", [""])[0]
            q = query.get("q", [""])[0]
            cfg = load_config()
            results = search_cover_candidates(code, q, cfg)
            return self._json(results)

        if parts == ["api", "cover", "search_sgdb"]:
            # Busca de capa no SteamGridDB pra escolha MANUAL - serve
            # Biblioteca e ROM pesada, que não têm as fontes dos
            # sistemas leves (libretro-thumbnails/LaunchBox/
            # ScreenScraper só cobrem leve + PS1, ver PLATFORM_MAP).
            # Pedido do usuário 28/08 pra poder "ir capeando todos os
            # jogos de todas as abas" na mão.
            q = query.get("q", [""])[0].strip()
            if len(q) < 2:
                return self._json([])
            cfg = load_config()
            api_key = cfg.get("steamgriddb", {}).get("api_key")
            if not api_key:
                return self._json({"error": "faltando api_key em [steamgriddb] no config.toml"}, 400)
            try:
                return self._json(library_mod.search_covers_steamgriddb(q, api_key))
            except (OSError, json.JSONDecodeError, KeyError) as e:
                return self._json({"error": f"falha na busca: {e}"}, 502)

        if parts == ["api", "cover", "ss_preview"]:
            # Proxy da imagem do ScreenScraper - a media_url real (com
            # senha embutida) nunca sai do backend, só os bytes da
            # imagem em si. Ver docstring de core/screenscraper.py.
            code = query.get("code", [""])[0]
            ss_id = query.get("id", [""])[0]
            media_url = _ss_media_cache.get(f"{code}:{ss_id}")
            if not media_url:
                self.send_response(404)
                self.end_headers()
                return
            data = screenscraper_mod.fetch_media_bytes(media_url)
            if not data:
                self.send_response(502)
                self.end_headers()
                return
            ctype = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parts == ["api", "organize", "pending"]:
            cfg = load_config()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            staging = cfg["pc"].get("organizar_dir", "0-Organizar")
            ext_index = organize_mod.build_ext_index(cfg["systems"], cfg.get("heavy_systems", {}))
            pending = organize_mod.list_pending(roms_root, staging, ext_index)
            return self._json({"staging_dir": staging, "items": pending})

        if parts == ["api", "heavy", "systems"]:
            cfg = load_config()
            heavy = heavy_mod.load_heavy_systems(cfg)
            return self._json([{"code": c, "nome": info.get("nome", c)} for c, info in heavy.items()])

        if parts[:3] == ["api", "heavy", "roms"] and len(parts) == 4:
            code = parts[3]
            cfg = load_config()
            heavy = heavy_mod.load_heavy_systems(cfg)
            sysinfo = heavy.get(code)
            if not sysinfo:
                return self._json({"error": "sistema pesado desconhecido"}, 404)
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            local_items = heavy_mod.list_local(code, roms_root, sysinfo.get("exts", []))
            local_by_name = {i["name"]: i for i in local_items}

            # Lado Drive vem do catálogo cacheado (cache/heavy_catalog.json,
            # o mesmo que o sortear usa) em vez de rclone ao vivo - pedido
            # do usuário (27/08): "manter um banco de dados das ROMs
            # pesadas... acha uma boa?" - sim, e já existia parcialmente
            # (heavy-catalog, construído pro sortear); só faltava a aba
            # de ROMs Pesadas usar também. list_drive_items ao vivo pode
            # levar ~90s por sistema (ver core/heavy_roms.py) - inviável
            # numa aba que o usuário troca com frequência. Sem cache
            # ainda (1a vez) cai pra live + já grava, populando o cache
            # sozinho pra próxima.
            catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)
            if code in catalog:
                drive_by_name = {item["name"]: item for item in catalog[code]}
            else:
                drive_items = heavy_mod.list_drive_items(code, cfg)
                drive_by_name = {i["name"]: i for i in drive_items}
                catalog[code] = sorted(drive_items, key=lambda i: i["name"])
                sortear_mod.save_heavy_catalog(HEAVY_CATALOG_PATH, catalog)

            android_ok = False
            remote_names = set()
            try:
                serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
                remote_names = heavy_mod.list_remote_names(code, cfg["android"]["jogos_root"], serial)
                android_ok = True
            except adb_mod.AdbError:
                pass

            # Confere no disco em vez de deixar o <img> da GUI tentar e
            # falhar (404 poluindo o console pra quem não tem match
            # exato ainda - PS1 nunca tem, ver COVERS_EXCLUDED) - mesma
            # checagem que /api/sortear já faz.
            capas_dir = None
            if sysinfo.get("capas"):
                capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
                capas_dir = capas_root / sysinfo["capas"] / "Named_Boxarts"

            # Cruza com a Biblioteca (mesmo comparador de nome+
            # plataforma de sempre, ver /api/covers e
            # find_for_rom/PLATAFORMA_ROM_CODES) pra mostrar iniciado/
            # finalizado/platinado/nota direto na galeria de ROM pesada
            # também (pedido do usuário 27/08: tracking universal, não
            # só leve) - só leitura aqui, a escrita é via
            # /api/library/track.
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            lib_by_norm = library_mod.index_by_rom_name(library_mod.load_library(library_path))

            def biblioteca_info(nome: str):
                g = library_mod.find_for_rom(lib_by_norm, nome, code)
                if not g:
                    return None
                return {"iniciado": g["iniciado"], "finalizado": g["finalizado"],
                        "platinado": g["platinado"], "nota": g["nota"]}

            out = []
            for name in sorted(set(local_by_name) | set(drive_by_name)):
                local = local_by_name.get(name)
                drive = drive_by_name.get(name)
                base = local or drive
                stem = name if base["is_dir"] else Path(name).stem
                capa = None
                if capas_dir:
                    for ext in (".png", ".jpg"):
                        if (capas_dir / f"{stem}{ext}").is_file():
                            capa = com_versao(f"/images/{code}/{urllib.parse.quote(stem + ext)}",
                                              capas_dir / f"{stem}{ext}")
                            break
                out.append({
                    "name": name, "size": base["size"], "is_dir": base["is_dir"],
                    "in_pc": local is not None, "in_drive": drive is not None,
                    "status": "no_celular" if (local and name in remote_names) else "so_pc",
                    "capa": capa,
                    "biblioteca": biblioteca_info(stem),
                })
            return self._json({"items": out, "android_ok": android_ok})

        if parts == ["api", "memcards"]:
            cfg = load_config()
            mc_cfg = cfg.get("memcards", {})
            out = []
            for console in ("ps1", "ps2"):
                for label, path in mc_cfg.get(console, {}).items():
                    out.append({
                        "console": console.upper(), "label": label, "key": f"{console}:{label}",
                        "tool_ok": memcard_mod.tool_available(console.upper()),
                    })
            return self._json(out)

        if parts[:3] == ["api", "memcards", "list"] and len(parts) == 4:
            key = urllib.parse.unquote(parts[3])
            path, console = self._memcard_path(key)
            if not path:
                return self._json({"error": "card desconhecido"}, 404)
            index = serials_mod.build_index()
            try:
                items = memcard_mod.list_card(console, path, index)
            except memcard_mod.MemcardError as e:
                return self._json({"error": str(e)}, 502)
            return self._json({"items": items})

        if parts[:3] == ["api", "emu_saves", "list"] and len(parts) == 4:
            emu = parts[3]
            if emu not in emu_saves_mod.EMULATORS:
                return self._json({"error": "emulador desconhecido"}, 404)
            cfg = load_config()
            index = serials_mod.build_index()
            local_names = emu_saves_mod.list_local(emu, cfg)
            android_ok = True
            try:
                remote_items = emu_saves_mod.list_remote(emu, cfg, index)
            except adb_mod.AdbError:
                remote_items = []
                android_ok = False
            for item in remote_items:
                item["in_pc"] = item["raw_name"] in local_names
            return self._json({"items": remote_items, "android_ok": android_ok})

        if parts == ["api", "fetch", "stream"]:
            job_id = query.get("job", [""])[0]
            with _jobs_lock:
                q = _jobs.get(job_id)
            if not q:
                return self._json({"error": "job desconhecido"}, 404)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            while True:
                event = q.get()
                chunk = f"data: {json.dumps(event)}\n\n".encode()
                try:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
                if event.get("type") == "job_done":
                    return

        self.send_response(404)
        self.end_headers()

    # Caminhos que fazem ler-modificar-gravar no library.json - todos
    # rodam sob _library_lock (ver comentário na declaração dela).
    _ESCRITA_BIBLIOTECA = {
        ("api", "library", "update"), ("api", "library", "track"),
        ("api", "library", "edit"), ("api", "library", "cover_upload"),
        ("api", "library", "decompor"),
        ("api", "cover", "apply_url"),
    }

    def do_POST(self):
        # Trava só o que mexe na biblioteca - o resto (disparo de job,
        # memory card, organize) segue em paralelo como sempre.
        rota = tuple(p for p in urllib.parse.urlparse(self.path).path.split("/") if p)
        try:
            if rota in self._ESCRITA_BIBLIOTECA:
                with _library_lock:
                    return self._do_POST()
            return self._do_POST()
        except Exception as e:
            return self._responder_erro(e)

    def _do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        query = urllib.parse.parse_qs(parsed.query)

        if parts == ["api", "settings"]:
            body = self._read_json_body()
            try:
                write_settings_paths(body)
            except Exception as e:
                return self._json({"error": str(e)}, 500)
            return self._json({"ok": True})

        if parts == ["api", "library", "decompor"]:
            # Decompõe uma coletânea nos jogos que ela contém (pedido do
            # usuário 29/08: "muitos jogos são collections, eventualmente
            # vou decompondo eles").
            #
            # O ponto crítico é o VÍNCULO: a pasta continua se chamando
            # "Portal Companion Collection" pra sempre, e a varredura
            # casa por nome - sem guardar esse nome como apelido de um
            # dos jogos resultantes, o próximo "🔄 Switch" recria a
            # coletânea do zero (foi exatamente o que aconteceu com o
            # Portal). Por isso o nome da coletânea vira `nomes_alt` do
            # primeiro jogo da lista.
            #
            # Jogo da lista que JÁ existe é reaproveitado, não duplicado
            # - é o caso comum: "Portal" já vinha da planilha, com nota
            # e finalizado, e não pode virar um registro novo vazio.
            body = self._read_json_body()
            game_id = body.get("id")
            nomes = [n.strip() for n in (body.get("nomes") or []) if n and n.strip()]
            if not nomes:
                return self._json({"error": "informe ao menos um jogo"}, 400)

            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            original = next((g for g in library["games"] if g["id"] == game_id), None)
            if not original:
                return self._json({"error": "jogo desconhecido"}, 404)

            plataforma, fontes = original["plataforma"], list(original["fontes"])
            # Todo nome que a coletânea já respondia por (o nome dela e
            # os apelidos que ela tinha) precisa continuar sendo
            # reconhecido depois que ela sumir.
            a_preservar = [original["nome"], *original.get("nomes_alt", [])]

            # Reaproveitamento é restrito à MESMA plataforma (29/08).
            # Antes olhava a biblioteca inteira só pelo nome, e isso
            # repetia o erro do Celeste: decompor "Final Fantasy 1-6
            # Bundle" do Switch encontraria o "Final Fantasy VI" que já
            # existe como ROM de SNES e enfiaria a fonte do Switch
            # dentro do registro do SNES - dois jogos diferentes virando
            # um. Nome só é identidade DENTRO de uma plataforma.
            por_nome = {}
            mesma_plataforma = [g for g in library["games"]
                                if g is not original and g["plataforma"] == plataforma]
            for g in mesma_plataforma:
                por_nome.setdefault(library_mod._normalize(g["nome"]), g)
            # Apelido só vale se o nome atual de ninguém já ocupou a
            # chave - mesma precedência de library.index_by_rom_name.
            for g in mesma_plataforma:
                for apelido in g.get("nomes_alt", []):
                    por_nome.setdefault(library_mod._normalize(apelido), g)

            resultantes, criados = [], 0
            for nome in nomes:
                existente = por_nome.get(library_mod._normalize(nome))
                if existente:
                    for f in fontes:
                        if f not in existente["fontes"]:
                            existente["fontes"].append(f)
                    resultantes.append(existente)
                    continue
                novo = library_mod._blank_game(nome, plataforma)
                novo["fontes"] = list(fontes)
                library["games"].append(novo)
                resultantes.append(novo)
                criados += 1

            principal = resultantes[0]
            conhecidos = {library_mod._normalize(n) for n in
                          [principal["nome"], *principal.get("nomes_alt", [])]}
            for nome in a_preservar:
                if library_mod._normalize(nome) not in conhecidos:
                    principal.setdefault("nomes_alt", []).append(nome)
                    conhecidos.add(library_mod._normalize(nome))

            # A coletânea some, a menos que ela mesma esteja na lista
            # (caso de "decompor" só pra renomear/anexar apelido).
            if original not in resultantes:
                library["games"].remove(original)

            library_mod.save_library(library_path, library)
            return self._json({"ok": True, "criados": criados,
                               "reaproveitados": len(resultantes) - criados,
                               "vinculo_em": principal["nome"],
                               "apelidos": principal.get("nomes_alt", [])})

        if parts == ["api", "library", "edit"]:
            # Edição de VÁRIOS campos de uma vez (popup "✎ Editar" da
            # Biblioteca) - o /update irmão grava um campo por vez, que
            # é o certo pra edição inline do card, mas ruim pra um
            # formulário inteiro (uma requisição por campo, e um erro no
            # meio deixaria metade salva). Aqui é tudo-ou-nada: valida
            # todos antes de gravar qualquer coisa.
            body = self._read_json_body()
            game_id, campos = body.get("id"), body.get("campos") or {}
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            if not any(g["id"] == game_id for g in library["games"]):
                return self._json({"error": "jogo desconhecido"}, 404)

            desconhecidos = [c for c in campos if c not in library_mod.EDITABLE_FIELDS]
            if desconhecidos:
                return self._json({"error": f"campo(s) não editável(is): {', '.join(desconhecidos)}"}, 400)

            # Valida numa cópia primeiro - assim um valor ruim no meio
            # não deixa o arquivo pela metade.
            ensaio = copy.deepcopy(library)
            try:
                for campo, valor in campos.items():
                    library_mod.update_game(ensaio, game_id, campo, valor)
            except (TypeError, ValueError) as e:
                return self._json({"error": str(e)}, 400)

            for campo, valor in campos.items():
                library_mod.update_game(library, game_id, campo, valor)
            library_mod.save_library(library_path, library)
            return self._json({"ok": True})

        if parts == ["api", "library", "update"]:
            # Edição inline (nota/tempo/iniciado/finalizado/platinado)
            # da aba Biblioteca - só esses campos, ver
            # core/library.EDITABLE_FIELDS. Funciona igual em modo
            # Android (leitura+escrita de arquivo local só).
            body = self._read_json_body()
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            try:
                ok = library_mod.update_game(library, body.get("id"), body.get("field"), body.get("value"))
            except (TypeError, ValueError):
                return self._json({"error": "valor inválido"}, 400)
            if not ok:
                return self._json({"error": "jogo ou campo desconhecido"}, 400)
            library_mod.save_library(library_path, library)
            return self._json({"ok": True})

        if parts == ["api", "library", "track"]:
            # Tracking universal (iniciado/finalizado/platinado/nota) pra
            # ROM leve ou pesada - pedido do usuário 27/08. Diferente de
            # /api/library/update (que já espera um "id" de jogo já
            # cadastrado), aqui a primeira edição feita na tela CRIA o
            # registro sozinha via get_or_create_for_rom - acha por nome
            # E plataforma compatível com `code` (nunca só nome: jogo
            # com nome igual em plataforma diferente é jogo DIFERENTE de
            # verdade, achado 27/08 sobre Celeste Xbox vs Celeste GBA -
            # ver core.library.PLATAFORMA_ROM_CODES); sem bater, cria um
            # registro novo com plataforma/fonte "rom:<CODIGO>".
            body = self._read_json_body()
            nome = (body.get("nome") or "").strip()
            code = (body.get("code") or "").strip()
            plataforma = (body.get("plataforma") or "").strip()
            fonte = (body.get("fonte") or "").strip()
            if not nome or not code or not plataforma or not fonte:
                return self._json({"error": "nome/code/plataforma/fonte obrigatorios"}, 400)
            cfg = load_config()
            library_path = Path(cfg["pc"]["library_root"]).expanduser() / "library.json"
            library = library_mod.load_library(library_path)
            game = library_mod.get_or_create_for_rom(library, nome, code, plataforma, fonte)
            try:
                ok = library_mod.update_game(library, game["id"], body.get("field"), body.get("value"))
            except (TypeError, ValueError):
                return self._json({"error": "valor inválido"}, 400)
            if not ok:
                return self._json({"error": "campo desconhecido"}, 400)
            library_mod.save_library(library_path, library)
            return self._json({"ok": True, "id": game["id"]})

        if parts == ["api", "cover", "apply_url"]:
            # Aplica uma capa escolhida na busca manual (ver
            # /api/cover/search_sgdb). Um endpoint só pros dois
            # destinos possíveis, porque a diferença é só ONDE grava:
            # ROM (leve ou pesada) vai pra capas_root/<sistema>/
            # Named_Boxarts/<label>.png; Biblioteca vai pra
            # library_root/capas/<id>.png. Mesmo cuidado do upload
            # manual: baixa e converte num temporário, só troca o
            # arquivo final depois de validar (ver /api/cover/upload).
            body = self._read_json_body()
            url = (body.get("url") or "").strip()
            if not url.startswith("https://"):
                return self._json({"error": "url inválida"}, 400)
            cfg = load_config()

            if body.get("kind") == "biblioteca":
                library_root = Path(cfg["pc"]["library_root"]).expanduser()
                library_path = library_root / "library.json"
                library = library_mod.load_library(library_path)
                game = next((g for g in library["games"] if g["id"] == body.get("id")), None)
                if not game:
                    return self._json({"error": "jogo desconhecido"}, 404)
                capas_dir, nome_base = library_root / "capas", game["id"]
            else:
                code, label = body.get("code"), body.get("label")
                capas_dir, info = self._cover_path(code, label)
                if not info:
                    return self._json({"error": "sistema desconhecido"}, 404)
                library, library_path, game = None, None, None
                nome_base = label

            try:
                req = urllib.request.Request(url, headers={"User-Agent": library_mod._BROWSER_USER_AGENT})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
            except OSError as e:
                return self._json({"error": f"falha ao baixar: {e}"}, 502)
            if len(data) < 100:
                return self._json({"error": "imagem vazia"}, 502)

            capas_dir.mkdir(parents=True, exist_ok=True)
            dest = capas_dir / f"{nome_base}.png"
            src_tmp = capas_dir / f"{nome_base}.src.tmp"
            dest_tmp = capas_dir / f"{nome_base}.dst.png.tmp"
            src_tmp.write_bytes(data)
            conv = subprocess.run(["convert", str(src_tmp), str(dest_tmp)], capture_output=True, text=True)
            src_tmp.unlink(missing_ok=True)
            if conv.returncode != 0 or not dest_tmp.exists() or dest_tmp.stat().st_size < 1000:
                dest_tmp.unlink(missing_ok=True)
                return self._json({"error": f"falha ao converter: {conv.stderr.strip()[:200]}"}, 500)
            dest_tmp.replace(dest)

            if game is not None:
                game["capa"] = f"capas/{nome_base}.png"
                library_mod.save_library(library_path, library)
                return self._json({"ok": True, "file": game["capa"]})

            old_jpg = capas_dir / f"{nome_base}.jpg"
            if old_jpg.exists():
                old_jpg.unlink()
            registry = load_registry()
            registry.setdefault(body.get("code"), {})[nome_base] = {"status": "manual", "source": "steamgriddb"}
            save_registry(registry)
            return self._json({"ok": True, "file": f"{nome_base}.png"})

        if parts == ["api", "library", "cover_upload"]:
            # Upload manual de capa pra jogo da Biblioteca - mesmo
            # tratamento de sempre (convert detecta o formato real pelo
            # conteúdo, não confia na extensão, ver /api/cover/upload),
            # só que gravando em library_root/capas/ em vez de
            # capas_root/<sistema>/Named_Boxarts/ (Biblioteca tem sua
            # própria pasta de capas, ver core/library.fetch_covers).
            body = self._read_json_body()
            game_id = body.get("id")
            filename, data_b64 = body.get("filename", ""), body.get("data", "")
            cfg = load_config()
            library_root = Path(cfg["pc"]["library_root"]).expanduser()
            library_path = library_root / "library.json"
            library = library_mod.load_library(library_path)
            game = next((g for g in library["games"] if g["id"] == game_id), None)
            if not game:
                return self._json({"error": "jogo desconhecido"}, 404)
            try:
                data = base64.b64decode(data_b64)
            except Exception as e:
                return self._json({"error": f"base64 inválido: {e}"}, 400)
            if len(data) < 100:
                return self._json({"error": "arquivo vazio ou pequeno demais"}, 400)

            capas_dir = library_root / "capas"
            capas_dir.mkdir(parents=True, exist_ok=True)
            dest = capas_dir / f"{game_id}.png"
            ext = Path(filename).suffix.lower() or ".png"
            tmp = capas_dir / f"{game_id}{ext}.tmp"
            tmp.write_bytes(data)
            conv = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
            tmp.unlink(missing_ok=True)
            if conv.returncode != 0 or not dest.exists() or dest.stat().st_size < 1000:
                return self._json({"error": f"falha ao converter pra png: {conv.stderr.strip()[:200]}"}, 500)
            game["capa"] = f"capas/{game_id}.png"
            library_mod.save_library(library_path, library)
            return self._json({"ok": True, "file": game["capa"]})

        if parts == ["api", "cover", "flag"]:
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            registry = load_registry()
            registry.setdefault(code, {})[label] = {"status": "flagged_wrong"}
            save_registry(registry)
            return self._json({"ok": True})

        if parts == ["api", "cover", "unflag"]:
            # tira do registro por completo - volta a ser "nunca processado",
            # pra próxima rodada de fetch-covers/fetch-covers-fallback poder
            # tentar achar uma correspondência de novo (nunca sobrescreve
            # sozinho, só limpa o estado - a decisão de baixar continua sendo
            # do usuário, rodando o fetch depois).
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            registry = load_registry()
            registry.get(code, {}).pop(label, None)
            save_registry(registry)
            return self._json({"ok": True})

        if parts == ["api", "cover", "duplicate"]:
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            registry = load_registry()
            registry.setdefault(code, {})[label] = {"status": "duplicate"}
            save_registry(registry)
            return self._json({"ok": True})

        if parts == ["api", "cover", "unduplicate"]:
            # mesma lógica do unflag - limpa o registro por completo, não
            # decide nada sozinho, só volta ao estado "não processado".
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            registry = load_registry()
            registry.get(code, {}).pop(label, None)
            save_registry(registry)
            return self._json({"ok": True})

        if parts == ["api", "cover", "rename"]:
            # Renomeia a capa E tenta a cascata (ROM + save/state) na
            # hora via core.rom_rename. Se a ROM não for encontrada (ou
            # tiver mais de uma batendo, ou já existir uma com o nome
            # novo), a capa ainda é renomeada mas o registro guarda
            # "renamed_pending" - mesmo mecanismo de antes, agora só
            # como fallback pro que a cascata não resolveu sozinha.
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            new_label_raw = (body.get("new_label") or "").strip()
            capas_dir, info = self._cover_path(code, label)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)
            if not new_label_raw:
                return self._json({"error": "nome novo vazio"}, 400)
            new_label = sanitize_mod.sanitize_name(new_label_raw)
            if new_label == label:
                return self._json({"error": "nome novo é igual ao atual"}, 400)

            src = None
            for ext in (".png", ".jpg", ".jpeg"):
                candidate = capas_dir / (label + ext)
                if candidate.exists():
                    src = candidate
                    break
            if not src:
                return self._json({"error": "capa atual não encontrada"}, 404)

            dest = capas_dir / (new_label + src.suffix)
            if dest.exists():
                return self._json({"error": f"já existe uma capa chamada '{new_label}'"}, 409)

            src.rename(dest)

            cfg = load_config()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            saves_dir = Path(cfg["pc"]["saves_root"]).expanduser()
            states_dir = Path(cfg["pc"]["states_root"]).expanduser()
            cascade = rom_rename_mod.rename_with_cascade(
                roms_root / code, saves_dir, states_dir, label, new_label, info.get("exts", []),
            )

            registry = load_registry()
            reg_sys = registry.setdefault(code, {})
            reg_sys.pop(label, None)
            if cascade["rom"]["status"] != "renomeado":
                reg_sys[new_label] = {
                    "status": "renamed_pending", "old_label": label,
                    "rom_status": cascade["rom"]["status"],
                }
            save_registry(registry)
            return self._json({
                "ok": True, "new_label": new_label, "file": new_label + src.suffix,
                "cascade": cascade,
            })

        if parts == ["api", "cover", "delete"]:
            # Apaga ROM + capa + save/state - usado pelo botão "🗑 Apagar"
            # de qualquer capa, e pra processar as marcadas como
            # duplicada. Sempre tenta apagar tudo, mesmo que algum lado
            # já não exista (limpa o que sobrou).
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            capas_dir, info = self._cover_path(code, label)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)

            cfg = load_config()
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            saves_dir = Path(cfg["pc"]["saves_root"]).expanduser()
            states_dir = Path(cfg["pc"]["states_root"]).expanduser()
            cascade = rom_rename_mod.delete_with_cascade(
                roms_root / code, capas_dir, saves_dir, states_dir, label, info.get("exts", []),
            )

            registry = load_registry()
            registry.get(code, {}).pop(label, None)
            save_registry(registry)
            return self._json({"ok": True, "cascade": cascade})

        if parts == ["api", "cover", "delete_save"]:
            # Apaga só o save OU state de um jogo (não a ROM/capa) -
            # botão 💾/⏱ na própria capa, pra sistemas RetroArch com
            # save/state achatado (saves_root/states_root, sem
            # subpasta por sistema - por isso não precisa do "code").
            body = self._read_json_body()
            label, kind = body.get("label"), body.get("kind")
            if kind not in ("save", "state"):
                return self._json({"error": "kind precisa ser 'save' ou 'state'"}, 400)
            cfg = load_config()
            folder = Path(cfg["pc"]["saves_root" if kind == "save" else "states_root"]).expanduser()
            deleted = rom_rename_mod.delete_flat_matches(folder, label)
            return self._json({"ok": True, "deleted": deleted})

        if parts == ["api", "cover", "upload"]:
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            filename, data_b64 = body.get("filename", ""), body.get("data", "")
            capas_dir, info = self._cover_path(code, label)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)
            capas_dir.mkdir(parents=True, exist_ok=True)
            ext = Path(filename).suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg"):
                return self._json({"error": f"extensão não suportada: {ext}"}, 400)
            try:
                data = base64.b64decode(data_b64)
            except Exception as e:
                return self._json({"error": f"base64 inválido: {e}"}, 400)
            if len(data) < 100:
                return self._json({"error": "arquivo vazio ou pequeno demais"}, 400)

            dest = capas_dir / (label + ".png")
            # Nunca confia na extensão que o navegador mandou pra decidir se
            # converte - achado em 02/08: várias capas da coleção real
            # tinham bytes JPEG de verdade salvos com nome .png (imagem
            # baixada do Google com extensão errada, por ex.), porque o
            # código antigo só convertia quando ext != ".png". Sempre passa
            # pelo `convert` do ImageMagick, que detecta o formato real pelo
            # conteúdo do arquivo, não pelo nome - idempotente e barato pra
            # um PNG de verdade.
            #
            # Converte pra um destino TEMPORÁRIO, não pro `dest` final -
            # achado 27/08 (bug sinalizado, corrigido agora): antes
            # convertia direto em cima de `dest`, e se a checagem de
            # tamanho abaixo falhasse (conversão "deu certo" mas resultou
            # num PNG minúsculo/corrompido), a capa antiga (ou a
            # inexistência de uma) ficava substituída pelo arquivo ruim
            # mesmo com o endpoint respondendo erro - só um PNG de origem
            # degenerado dispara isso na prática, mas sem aviso nenhum
            # pro usuário de que o disco mudou. Agora só troca pra `dest`
            # de verdade (rename atômico) depois de validar - falha nunca
            # mais mexe no que já existia.
            src_tmp = capas_dir / (label + ".src" + ext + ".tmp")
            dest_tmp = capas_dir / (label + ".dst.png.tmp")
            src_tmp.write_bytes(data)
            conv = subprocess.run(["convert", str(src_tmp), str(dest_tmp)], capture_output=True, text=True)
            src_tmp.unlink(missing_ok=True)
            if conv.returncode != 0 or not dest_tmp.exists() or dest_tmp.stat().st_size < 1000:
                dest_tmp.unlink(missing_ok=True)
                return self._json({"error": f"falha ao converter pra png: {conv.stderr.strip()[:200]}"}, 500)
            dest_tmp.replace(dest)
            old_jpg = capas_dir / (label + ".jpg")
            if old_jpg.exists():
                old_jpg.unlink()
            registry = load_registry()
            registry.setdefault(code, {})[label] = {"status": "manual"}
            save_registry(registry)
            return self._json({"ok": True, "file": label + ".png"})

        if parts == ["api", "cover", "select"]:
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            source, name = body.get("source"), body.get("name")
            filename = body.get("filename", "")
            capas_dir, info = self._cover_path(code, label)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)
            capas_dir.mkdir(parents=True, exist_ok=True)
            dest = capas_dir / (label + ".png")
            if source == "screenscraper":
                ss_id = body.get("ss_id", "")
                media_url = _ss_media_cache.get(f"{code}:{ss_id}")
                ok = screenscraper_mod.download_cover(media_url, dest) if media_url else False
            else:
                ok = download_selected_cover(source, name, info["repo"], filename, dest)
            if not ok:
                return self._json({"error": "download falhou"}, 502)
            old_jpg = capas_dir / (label + ".jpg")
            if old_jpg.exists():
                old_jpg.unlink()
            registry = load_registry()
            registry.setdefault(code, {})[label] = {"status": "manual", "matched": name, "source": source}
            save_registry(registry)
            return self._json({"ok": True})

        if parts[:2] == ["api", "fetch"] and len(parts) == 3:
            code = parts[2]
            apply = query.get("apply", ["0"])[0] == "1"
            fallback = query.get("fallback", [""])[0]
            if fallback == "0":
                fallback = ""

            job_id = f"{code}-{threading.get_ident()}-{id(object())}"
            q: "queue.Queue" = queue.Queue()
            with _jobs_lock:
                _jobs[job_id] = q

            t = threading.Thread(target=run_fetch_job, args=(job_id, code, apply, fallback), daemon=True)
            t.start()
            return self._json({"job": job_id})

        if parts == ["api", "library", "refresh"]:
            source = query.get("source", [""])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_library_refresh_job(emit, source, apply))
            return self._json({"job": job_id})

        if parts == ["api", "library", "add"]:
            body = self._read_json_body()
            games, plataforma, fonte = body.get("games", ""), body.get("plataforma", ""), body.get("fonte", "")
            apply = bool(body.get("apply"))
            job_id = _start_job(lambda emit: run_library_add_job(emit, games, plataforma, fonte, apply))
            return self._json({"job": job_id})

        if parts == ["api", "library", "fetch_covers"]:
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_library_fetch_covers_job(emit, apply))
            return self._json({"job": job_id})

        if parts == ["api", "heavy_catalog"]:
            job_id = _start_job(run_heavy_catalog_job)
            return self._json({"job": job_id})

        if parts == ["api", "heavy", "fetch_covers"]:
            code = query.get("code", [""])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_heavy_fetch_covers_job(emit, code, apply))
            return self._json({"job": job_id})

        if parts == ["api", "backup_config"]:
            target = query.get("target", ["all"])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_backup_config_job(emit, target, apply))
            return self._json({"job": job_id})

        if parts == ["api", "backup_saves"]:
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_backup_saves_job(emit, apply))
            return self._json({"job": job_id})

        if parts == ["api", "sanitize_names"]:
            target = query.get("target", ["all"])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_sanitize_names_job(emit, target, apply))
            return self._json({"job": job_id})

        if parts[:2] == ["api", "rebuild_playlist"] and len(parts) == 3:
            code = parts[2]
            target = query.get("target", ["all"])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_rebuild_playlist_job(emit, code, target, apply))
            return self._json({"job": job_id})

        if parts == ["api", "emu_sync"]:
            source = query.get("source", ["all"])[0]
            apply = query.get("apply", ["0"])[0] == "1"
            job_id = _start_job(lambda emit: run_emu_sync_job(emit, source, apply))
            return self._json({"job": job_id})

        if parts == ["api", "organize", "move"]:
            body = self._read_json_body()
            name, code = body.get("name"), body.get("code")
            if not name or not code:
                return self._json({"error": "name e code obrigatorios"}, 400)
            cfg = load_config()
            if code not in cfg["systems"] and code not in cfg.get("heavy_systems", {}):
                return self._json({"error": "sistema desconhecido"}, 404)
            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            staging = cfg["pc"].get("organizar_dir", "0-Organizar")
            ok, msg = organize_mod.move_to_system(roms_root, staging, name, code)
            if not ok:
                return self._json({"error": msg}, 409)

            # Tenta já sair capeado do organizar, em vez de esperar uma
            # rodada manual de "Buscar capas" depois - só pra sistemas
            # leves com capas (heavy_systems e PS/SDC não têm galeria de
            # capa, ver COVERS_EXCLUDED). Falha de rede aqui nunca
            # desfaz o move, que já aconteceu de verdade.
            cover_status = None
            info = cfg["systems"].get(code)
            if info and code not in covers_mod.COVERS_EXCLUDED:
                dest_name = organize_mod.clean_name(name)
                label = Path(dest_name).stem
                capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
                capas_dir = capas_root / info["capas"] / "Named_Boxarts"
                try:
                    names = covers_mod.load_tree(info["repo"])
                    exact_idx = covers_mod.build_index(names, loose=False)
                    loose_idx = covers_mod.build_index(names, loose=True)
                    norm_keys = list(exact_idx.keys())
                    romname_dat = arcade_romname_dat(code)
                    cover_status, _ = covers_mod.fetch_one(
                        label, info["repo"], capas_dir, exact_idx, loose_idx, norm_keys, romname_dat
                    )
                except Exception:
                    cover_status = None

            return self._json({"ok": True, "message": msg, "cover": cover_status})

        if parts == ["api", "heavy", "send"]:
            body = self._read_json_body()
            code, name = body.get("code"), body.get("name")
            overwrite = bool(body.get("overwrite"))
            if not code or not name:
                return self._json({"error": "code e name obrigatorios"}, 400)

            job_id = f"heavy-{code}-{threading.get_ident()}-{id(object())}"
            q: "queue.Queue" = queue.Queue()
            with _jobs_lock:
                _jobs[job_id] = q

            t = threading.Thread(target=run_heavy_send_job, args=(job_id, code, name, overwrite), daemon=True)
            t.start()
            return self._json({"job": job_id})

        if parts == ["api", "heavy", "download"]:
            body = self._read_json_body()
            code, name = body.get("code"), body.get("name")
            if not code or not name:
                return self._json({"error": "code e name obrigatorios"}, 400)

            job_id = f"heavydl-{code}-{threading.get_ident()}-{id(object())}"
            q: "queue.Queue" = queue.Queue()
            with _jobs_lock:
                _jobs[job_id] = q

            t = threading.Thread(target=run_heavy_download_job, args=(job_id, code, name), daemon=True)
            t.start()
            return self._json({"job": job_id})

        if parts == ["api", "heavy", "rename"]:
            body = self._read_json_body()
            code = body.get("code")
            old_label = body.get("old_label")
            new_label_raw = (body.get("new_label") or "").strip()
            cfg = load_config()
            heavy = heavy_mod.load_heavy_systems(cfg)
            sysinfo = heavy.get(code)
            if not sysinfo:
                return self._json({"error": "sistema pesado desconhecido"}, 404)
            if not old_label or not new_label_raw:
                return self._json({"error": "nome novo/antigo vazio"}, 400)
            new_label = sanitize_mod.sanitize_name(new_label_raw)
            if new_label == old_label:
                return self._json({"error": "nome novo é igual ao atual"}, 400)

            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            saves_dir = Path(cfg["pc"]["saves_root"]).expanduser()
            states_dir = Path(cfg["pc"]["states_root"]).expanduser()
            cascade = rom_rename_mod.rename_with_cascade(
                roms_root / code, saves_dir, states_dir, old_label, new_label, sysinfo.get("exts", []),
            )
            rom_status = cascade["rom"]["status"]
            if rom_status != "renomeado":
                msg = {
                    "nao_encontrado": "ROM não encontrada",
                    "conflito": "já existe um item com esse nome",
                    "ambiguo": "mais de um arquivo bate com esse nome - resolva manualmente",
                }.get(rom_status, "falhou")
                status_code = 409 if rom_status == "conflito" else 404
                return self._json({"error": msg}, status_code)
            return self._json({"ok": True, "new_label": new_label, "cascade": cascade})

        if parts == ["api", "heavy", "delete"]:
            body = self._read_json_body()
            code, label = body.get("code"), body.get("label")
            cfg = load_config()
            heavy = heavy_mod.load_heavy_systems(cfg)
            sysinfo = heavy.get(code)
            if not sysinfo:
                return self._json({"error": "sistema pesado desconhecido"}, 404)
            if not label:
                return self._json({"error": "label vazio"}, 400)

            roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
            saves_dir = Path(cfg["pc"]["saves_root"]).expanduser()
            states_dir = Path(cfg["pc"]["states_root"]).expanduser()
            cascade = rom_rename_mod.delete_with_cascade(
                roms_root / code, None, saves_dir, states_dir, label, sysinfo.get("exts", []),
            )
            return self._json({"ok": True, "cascade": cascade})

        if parts == ["api", "memcards", "add"]:
            body = self._read_json_body()
            console = (body.get("console") or "").lower()
            label = (body.get("label") or "").strip()
            raw_path = (body.get("path") or "").strip()
            mode = body.get("mode")  # "create" (card em branco novo) ou "open" (card já existente)
            if console not in ("ps1", "ps2"):
                return self._json({"error": "console inválido"}, 400)
            if not label or not raw_path:
                return self._json({"error": "nome e caminho são obrigatórios"}, 400)
            cfg = load_config()
            existing = cfg.get("memcards", {}).get(console, {})
            if label in existing:
                return self._json({"error": f'já existe um card chamado "{label}"'}, 409)
            dest = Path(raw_path).expanduser()
            if mode == "create":
                if not existing:
                    return self._json({
                        "error": "precisa de pelo menos um card desse console já configurado "
                                 "pra servir de molde"
                    }, 400)
                template_path = Path(next(iter(existing.values()))).expanduser()
                try:
                    memcard_mod.create_card(console.upper(), template_path, dest)
                except (memcard_mod.MemcardError, OSError) as e:
                    return self._json({"error": str(e)}, 502)
            else:
                if not dest.exists():
                    return self._json({"error": "arquivo não encontrado"}, 404)
                try:
                    memcard_mod.mc_info(console.upper(), dest)
                except memcard_mod.MemcardError as e:
                    return self._json({"error": f"não parece ser um card válido: {e}"}, 502)
            add_memcard_entry(console, label, raw_path)
            return self._json({"ok": True, "key": f"{console}:{label}"})

        if parts == ["api", "memcards", "remove"]:
            body = self._read_json_body()
            console = (body.get("console") or "").lower()
            label = body.get("label") or ""
            if not remove_memcard_entry(console, label):
                return self._json({"error": "card não encontrado em config.toml"}, 404)
            return self._json({"ok": True})

        if parts == ["api", "memcards", "export"]:
            body = self._read_json_body()
            key, item = body.get("key", ""), body.get("item")
            path, console = self._memcard_path(key)
            if not item:
                return self._json({"error": "item vazio"}, 400)
            if not path:
                return self._json({"error": "card desconhecido"}, 404)
            cfg = load_config()
            export_dir = Path(cfg.get("memcards", {}).get("export_dir", "~/Downloads")).expanduser()
            try:
                dest = memcard_mod.export_save(console, path, item, export_dir)
            except memcard_mod.MemcardError as e:
                return self._json({"error": str(e)}, 502)
            return self._json({"ok": True, "file": str(dest)})

        if parts == ["api", "memcards", "delete"]:
            body = self._read_json_body()
            key, item = body.get("key", ""), body.get("item")
            path, console = self._memcard_path(key)
            if not item:
                return self._json({"error": "item vazio"}, 400)
            if not path:
                return self._json({"error": "card desconhecido"}, 404)
            try:
                memcard_mod.delete_save(console, path, item)
            except memcard_mod.MemcardError as e:
                return self._json({"error": str(e)}, 502)
            return self._json({"ok": True})

        if parts == ["api", "memcards", "import"]:
            body = self._read_json_body()
            key = body.get("key", "")
            filename, data_b64 = body.get("filename", ""), body.get("data", "")
            path, console = self._memcard_path(key)
            if not path:
                return self._json({"error": "card desconhecido"}, 404)
            try:
                data = base64.b64decode(data_b64)
            except Exception as e:
                return self._json({"error": f"base64 inválido: {e}"}, 400)
            if len(data) < 100:
                return self._json({"error": "arquivo vazio ou pequeno demais"}, 400)
            ext = Path(filename).suffix or ".mcs"
            # import_save() decide o formato pela extensão do arquivo
            # (src_file.suffix) - ela tem que ficar por último no nome,
            # não pode ter ".tmp" depois ou ele lê ".tmp" como formato.
            tmp = path.with_name(path.name + f".import.tmp{ext}")
            tmp.write_bytes(data)
            try:
                memcard_mod.import_save(console, path, tmp)
            except memcard_mod.MemcardError as e:
                return self._json({"error": str(e)}, 502)
            finally:
                tmp.unlink(missing_ok=True)
            return self._json({"ok": True})

        if parts == ["api", "memcards", "transfer"]:
            body = self._read_json_body()
            src_key, dest_key, item = body.get("src_key", ""), body.get("dest_key", ""), body.get("item")
            src_path, src_console = self._memcard_path(src_key)
            dest_path, dest_console = self._memcard_path(dest_key)
            if not item:
                return self._json({"error": "item vazio"}, 400)
            if not src_path or not dest_path:
                return self._json({"error": "card desconhecido"}, 404)
            if src_console != dest_console:
                return self._json({"error": "só é possível transferir entre cards do mesmo console"}, 400)
            cfg = load_config()
            tmp_dir = Path(cfg.get("memcards", {}).get("export_dir", "~/Downloads")).expanduser()
            try:
                memcard_mod.transfer_save(src_console, src_path, dest_path, item, tmp_dir)
            except memcard_mod.MemcardError as e:
                return self._json({"error": str(e)}, 502)
            return self._json({"ok": True})

        if parts == ["api", "emu_saves", "pull"]:
            body = self._read_json_body()
            emu, item = body.get("emu", ""), body.get("item")
            if emu not in emu_saves_mod.EMULATORS:
                return self._json({"error": "emulador desconhecido"}, 404)
            if not item:
                return self._json({"error": "item vazio"}, 400)
            cfg = load_config()
            try:
                dest = emu_saves_mod.pull_item(emu, item, cfg)
            except adb_mod.AdbError as e:
                return self._json({"error": str(e)}, 502)
            return self._json({"ok": True, "file": str(dest)})

        self.send_response(404)
        self.end_headers()


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"PyRetro GUI rodando em http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
