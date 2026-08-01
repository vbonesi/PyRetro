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
import json
import queue
import sys
import threading
import tomllib
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import covers as covers_mod
from core import launchbox as launchbox_mod

CONFIG_PATH = ROOT / "config.toml"
REGISTRY_PATH = ROOT / "cache" / "covers_registry.json"
STATIC_DIR = Path(__file__).parent / "static"

# PS1 e Dreamcast saíram da biblioteca de capas (os standalones DuckStation/
# Flycast baixam capa sozinhos agora - ver docs/capas_sem_correspondencia.md).
# Continuam no config.toml normalmente pra quando ROMs/Saves existirem na
# GUI - essa exclusão é só da TELA DE CAPAS, não do projeto como um todo.
COVERS_EXCLUDED = {"SDC", "PS"}

_jobs: dict[str, "queue.Queue"] = {}
_jobs_lock = threading.Lock()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config.toml não encontrado - copie config.example.toml para {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


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
            files = sorted(p.name for p in capas_dir.iterdir() if p.suffix.lower() in (".png", ".jpg"))
            return self._json(files)

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
