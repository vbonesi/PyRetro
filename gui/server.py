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
import json
import queue
import re
import subprocess
import sys
import threading
import tomllib
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import adb as adb_mod
from core import covers as covers_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import organize as organize_mod
from core import rom_rename as rom_rename_mod
from core import sanitize as sanitize_mod

CONFIG_PATH = ROOT / "config.toml"
REGISTRY_PATH = ROOT / "cache" / "covers_registry.json"
STATIC_DIR = Path(__file__).parent / "static"

COVERS_EXCLUDED = covers_mod.COVERS_EXCLUDED

_jobs: dict[str, "queue.Queue"] = {}
_jobs_lock = threading.Lock()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config.toml não encontrado - copie config.example.toml para {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def search_cover_candidates(code: str, query: str, systems_cfg: dict) -> list:
    """Busca por substring (não exata, não fuzzy com trava - aqui quem
    decide é o humano olhando a prévia) nas duas fontes já integradas.
    Usado pela tela de "capa errada, buscar outra opção"."""
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


def run_fetch_job(job_id: str, code: str, apply: bool, use_fallback: bool) -> None:
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

            if not use_fallback:
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
            else:
                if sys_code not in launchbox_mod.PLATFORM_MAP:
                    continue
                index = launchbox_mod.build_index()

                def on_progress(label, status, i, total, _code=sys_code):
                    emit({"type": "progress", "code": _code, "label": label, "status": status, "i": i, "total": total})

                found = launchbox_mod.process_system_fallback(
                    sys_code, sysinfo["capas"], capas_root, registry, index, apply=apply, on_progress=on_progress,
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
                })
            return self._json(out)

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
            out = []
            for f in files:
                label = Path(f).stem
                status = reg_sys.get(label, {}).get("status")
                out.append({
                "file": f, "label": label, "status": status,
                "flagged": status == "flagged_wrong", "duplicated": status == "duplicate",
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
            results = search_cover_candidates(code, q, cfg["systems"])
            return self._json(results)

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
            items = heavy_mod.list_local(code, roms_root, sysinfo.get("exts", []))

            android_ok = False
            remote_names = set()
            try:
                serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
                remote_names = heavy_mod.list_remote_names(code, cfg["android"]["jogos_root"], serial)
                android_ok = True
            except adb_mod.AdbError:
                pass

            out = [{**item, "status": "no_celular" if item["name"] in remote_names else "so_pc"} for item in items]
            return self._json({"items": out, "android_ok": android_ok})

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
            fallback = query.get("fallback", ["0"])[0] == "1"

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
