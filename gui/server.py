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
import json
import queue
import re
import subprocess
import sys
import threading
import tomllib
import unicodedata
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import adb as adb_mod
from core import covers as covers_mod
from core import emu_saves as emu_saves_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import memcard as memcard_mod
from core import organize as organize_mod
from core import rom_rename as rom_rename_mod
from core import sanitize as sanitize_mod
from core import screenscraper as screenscraper_mod
from core import serials as serials_mod

CONFIG_PATH = ROOT / "config.toml"
REGISTRY_PATH = ROOT / "cache" / "covers_registry.json"
STATIC_DIR = Path(__file__).parent / "static"

COVERS_EXCLUDED = covers_mod.COVERS_EXCLUDED

_jobs: dict[str, "queue.Queue"] = {}
_jobs_lock = threading.Lock()

# "code:ss_id" -> media_url real do ScreenScraper (com credenciais
# embutidas) - NUNCA mandado pro cliente, só usado pelo proxy de
# preview e pelo download final. Em memória, por processo - some ao
# reiniciar o servidor, o que é aceitável (busca de novo re-popula).
_ss_media_cache: dict[str, str] = {}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config.toml não encontrado - copie config.example.toml para {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def search_cover_candidates(code: str, query: str, cfg: dict) -> list:
    """Busca por substring (não exata, não fuzzy com trava - aqui quem
    decide é o humano olhando a prévia) nas três fontes integradas.
    Usado pela tela de "capa errada, buscar outra opção"."""
    systems_cfg = cfg["systems"]
    sysinfo = systems_cfg.get(code)
    if not sysinfo:
        return []
    q_norm = covers_mod.normalize(query)
    if not q_norm:
        return []
    results = []

    repo = sysinfo["repo"]
    base_url = f"https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/Named_Boxarts/"
    for name in covers_mod.load_tree(repo):
        if q_norm in covers_mod.normalize(name):
            results.append({
                "source": "libretro", "name": name,
                "preview": base_url + urllib.parse.quote(name + ".png"),
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
        diretório Named_Boxarts dela. Retorna (None, None) se o sistema
        não existir no config.toml."""
        cfg = load_config()
        info = cfg["systems"].get(code)
        if not info:
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

    def _file(self, path: Path, content_type: str):
        if not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        if parts[:1] == ["static"] and len(parts) == 2:
            ext = parts[1].rsplit(".", 1)[-1]
            ctype = {"js": "application/javascript", "css": "text/css"}.get(ext, "application/octet-stream")
            return self._file(STATIC_DIR / parts[1], ctype)

        if parts[:2] == ["api", "systems"]:
            cfg = load_config()
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            registry = load_registry()
            out = []
            for code, info in cfg["systems"].items():
                if code in COVERS_EXCLUDED:
                    continue
                capas_dir = capas_root / info["capas"] / "Named_Boxarts"
                count = len(list(capas_dir.glob("*.png"))) + len(list(capas_dir.glob("*.jpg"))) if capas_dir.is_dir() else 0
                no_match = sum(1 for v in registry.get(code, {}).values() if v.get("status") == "no_match")
                out.append({
                    "code": code, "capas": info["capas"], "count": count,
                    "no_match": no_match, "has_launchbox": code in launchbox_mod.PLATFORM_MAP,
                    "has_screenscraper": code in screenscraper_mod.SYSTEM_MAP,
                })
            return self._json(out)

        if parts == ["api", "search_library"]:
            # Busca geral - pedido do usuário pra achar um jogo sem
            # precisar já saber em qual sistema ele está. Substring
            # simples (case/acento-insensitive), não a normalização
            # "agressiva" de covers.normalize (que tira tag/artigo/
            # parênteses - certa pra decidir se dois resultados são o
            # mesmo jogo, errada pra busca livre onde o usuário pode
            # digitar exatamente uma tag tipo "usa").
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
                for p in capas_dir.iterdir():
                    if p.suffix.lower() not in (".png", ".jpg"):
                        continue
                    label = p.stem
                    label_norm = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode().lower()
                    if q_norm in label_norm:
                        out.append({"code": code, "label": label, "file": p.name})
            out.sort(key=lambda x: (x["label"].lower(), x["code"]))
            return self._json(out[:100])

        if parts[:2] == ["api", "covers"] and len(parts) == 3:
            code = parts[2]
            cfg = load_config()
            info = cfg["systems"].get(code)
            if not info:
                return self._json({"error": "sistema desconhecido"}, 404)
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            capas_dir = capas_root / info["capas"] / "Named_Boxarts"
            if not capas_dir.is_dir():
                return self._json([])
            registry = load_registry()
            reg_sys = registry.get(code, {})
            files = sorted(p.name for p in capas_dir.iterdir() if p.suffix.lower() in (".png", ".jpg"))
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

            out = []
            for f in files:
                label = Path(f).stem
                status = reg_sys.get(label, {}).get("status")
                out.append({
                "file": f, "label": label, "status": status,
                "flagged": status == "flagged_wrong", "duplicated": status == "duplicate",
                "has_save": has_flat_match(saves_names, label), "has_state": has_flat_match(states_names, label),
            })
            return self._json(out)

        if parts[:1] == ["images"] and len(parts) >= 3:
            code = parts[1]
            filename = urllib.parse.unquote("/".join(parts[2:]))
            cfg = load_config()
            info = cfg["systems"].get(code)
            if not info:
                return self._file(Path("/nonexistent"), "image/png")
            capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
            path = capas_root / info["capas"] / "Named_Boxarts" / filename
            ctype = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            return self._file(path, ctype)

        if parts == ["api", "settings"]:
            cfg = load_config()
            return self._json({"pc": cfg.get("pc", {}), "android": cfg.get("android", {})})

        if parts == ["api", "cover", "search"]:
            code = query.get("code", [""])[0]
            q = query.get("q", [""])[0]
            cfg = load_config()
            results = search_cover_candidates(code, q, cfg)
            return self._json(results)

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
            drive_by_name = {i["name"]: i for i in heavy_mod.list_drive_items(code, cfg)}

            android_ok = False
            remote_names = set()
            try:
                serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
                remote_names = heavy_mod.list_remote_names(code, cfg["android"]["jogos_root"], serial)
                android_ok = True
            except adb_mod.AdbError:
                pass

            out = []
            for name in sorted(set(local_by_name) | set(drive_by_name)):
                local = local_by_name.get(name)
                drive = drive_by_name.get(name)
                base = local or drive
                out.append({
                    "name": name, "size": base["size"], "is_dir": base["is_dir"],
                    "in_pc": local is not None, "in_drive": drive is not None,
                    "status": "no_celular" if (local and name in remote_names) else "so_pc",
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

    def do_POST(self):
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
            tmp = capas_dir / (label + ext + ".tmp")
            tmp.write_bytes(data)
            conv = subprocess.run(["convert", str(tmp), str(dest)], capture_output=True, text=True)
            tmp.unlink(missing_ok=True)
            if conv.returncode != 0 or not dest.exists() or dest.stat().st_size < 1000:
                return self._json({"error": f"falha ao converter pra png: {conv.stderr.strip()[:200]}"}, 500)
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
            return self._json({"ok": True, "message": msg})

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
