"""
Sincronização PC <-> Android: por enquanto só capas (Named_Boxarts) -
saves/states/runtime-logs ficam pra depois, mesma arquitetura (ver
docs/roadmap.md, "modo PC via adb").

Regras (definidas no planejamento, não mudar sem revisitar o motivo):
    - Nunca deleta. Só copia adição/atualização. Remoção é um comando
      separado e explícito, com confirmação.
    - "Mais recente vence" só quando apenas um lado mudou desde o
      último manifesto (cache/sync_state.json). Se os dois lados
      mudaram desde a última sync (conflito real), não decide sozinho
      - lista pra revisão manual. Sem manifesto anterior (primeira
      sync desse arquivo) e os mtimes batem, marca sem_mudanca; se não
      batem, também vira conflito - não dá pra saber qual lado é o
      "certo" sem baseline.
    - dry-run por padrão; só escreve com --apply.
"""
import json
from pathlib import Path

from core import adb as adb_mod
from core.covers import COVERS_EXCLUDED

STATE_PATH = Path(__file__).parent.parent / "cache" / "sync_state.json"

# FAT32/exFAT no armazenamento Android arredonda timestamp (historicamente
# em passos de 2s) - folga pra não marcar "mudou" um arquivo que só teve o
# mtime arredondado na cópia.
MTIME_EPSILON = 2.0


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1, ensure_ascii=False))


def _local_mtimes(pc_dir: Path) -> dict:
    if not pc_dir.is_dir():
        return {}
    return {str(p.relative_to(pc_dir)): p.stat().st_mtime for p in pc_dir.rglob("*") if p.is_file()}


def _remote_mtimes(android_dir: str, serial: str | None) -> dict:
    """Uma chamada adb só (find + stat), não uma por arquivo - a coleção
    tem centenas/milhares de capas e cada chamada adb tem overhead de
    processo. Usa `stat -c` via find -exec (toybox no Android moderno
    suporta os dois) em vez de `find -printf`, por portabilidade - não
    deu pra testar contra o aparelho real nesta sessão (telefone
    desconectado), preferi a opção mais compatível entre versões do
    toybox/busybox."""
    android_dir = android_dir.rstrip("/")
    out = adb_mod.shell(
        f"find '{android_dir}' -type f -exec stat -c '%Y %n' {{}} \\; 2>/dev/null",
        serial=serial,
    )
    prefix = android_dir + "/"
    result = {}
    for line in out.splitlines():
        line = line.rstrip("\n")
        if " " not in line:
            continue
        mtime_s, path = line.split(" ", 1)
        try:
            mtime = float(mtime_s)
        except ValueError:
            continue
        relpath = path[len(prefix):] if path.startswith(prefix) else path
        result[relpath] = mtime
    return result


def scan_pair(pc_dir: Path, android_dir: str, prev_state: dict, serial: str | None = None) -> dict:
    """Compara os dois lados (mtime local via os.stat, mtime remoto via
    um find+stat só) contra o manifesto do último sync bem-sucedido e
    classifica cada arquivo. Nunca decide sozinho quando os dois lados
    mudaram desde a última sync - isso vira 'conflito' pra revisão
    manual. Retorna {local, remote, classified} - local/remote ficam
    disponíveis pra quem chamar não precisar rescanear pra atualizar o
    manifesto depois."""
    local = _local_mtimes(pc_dir)
    remote = _remote_mtimes(android_dir, serial)

    classified = {"sem_mudanca": [], "copiar_pra_pc": [], "copiar_pro_android": [], "conflito": []}
    for relpath in sorted(set(local) | set(remote)):
        lm = local.get(relpath)
        rm = remote.get(relpath)

        if lm is not None and rm is None:
            classified["copiar_pro_android"].append(relpath)
            continue
        if lm is None and rm is not None:
            classified["copiar_pra_pc"].append(relpath)
            continue

        prev = prev_state.get(relpath)
        if prev is None:
            key = "sem_mudanca" if abs(lm - rm) <= MTIME_EPSILON else "conflito"
            classified[key].append(relpath)
            continue

        pc_changed = abs(lm - prev.get("mtime_pc", lm)) > MTIME_EPSILON
        android_changed = abs(rm - prev.get("mtime_android", rm)) > MTIME_EPSILON

        if not pc_changed and not android_changed:
            classified["sem_mudanca"].append(relpath)
        elif pc_changed and not android_changed:
            classified["copiar_pro_android"].append(relpath)
        elif android_changed and not pc_changed:
            classified["copiar_pra_pc"].append(relpath)
        else:
            classified["conflito"].append(relpath)

    return {"local": local, "remote": remote, "classified": classified}


def sync_capas(cfg: dict, dry_run: bool = True, on_progress=None) -> dict:
    """Sincroniza Named_Boxarts (capas) PC <-> Android, sistema por
    sistema. SDC e PS ficam fora - saíram da biblioteca de capas do
    PyRetro (standalones DuckStation/Flycast baixam sozinhos), mesma
    exclusão da tela de capas da GUI (core.covers.COVERS_EXCLUDED).

    on_progress(code, relpath, direction), se passado, é chamado a cada
    arquivo copiado - direction é 'pro_android' ou 'pra_pc'."""
    pc_capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    android_cfg = cfg["android"]
    android_thumbs_root = android_cfg["thumbnails_root"]
    serial = adb_mod.ensure_connected(android_cfg.get("device_serial") or None)

    state = load_state()
    state_capas = state.setdefault("capas", {})

    report = {"copiado_pro_android": 0, "copiado_pra_pc": 0, "sem_mudanca": 0, "conflitos": [], "erros": []}

    for code, sysinfo in cfg["systems"].items():
        if code in COVERS_EXCLUDED:
            continue
        pc_dir = pc_capas_root / sysinfo["capas"] / "Named_Boxarts"
        if not pc_dir.is_dir():
            continue
        android_dir = f"{android_thumbs_root}/{sysinfo['capas']}/Named_Boxarts"

        scan = scan_pair(pc_dir, android_dir, state_capas.get(code, {}), serial=serial)
        classified = scan["classified"]
        sys_state = state_capas.setdefault(code, {})

        report["sem_mudanca"] += len(classified["sem_mudanca"])
        report["conflitos"] += [f"{code}/{r}" for r in classified["conflito"]]

        for relpath in classified["copiar_pro_android"]:
            if on_progress:
                on_progress(code, relpath, "pro_android")
            if dry_run:
                report["copiado_pro_android"] += 1
                continue
            local_path = pc_dir / relpath
            remote_path = f"{android_dir}/{relpath}"
            if adb_mod.push(local_path, remote_path, serial=serial):
                mtime = local_path.stat().st_mtime
                sys_state[relpath] = {"mtime_pc": mtime, "mtime_android": mtime}
                report["copiado_pro_android"] += 1
            else:
                report["erros"].append(f"push falhou: {code}/{relpath}")

        for relpath in classified["copiar_pra_pc"]:
            if on_progress:
                on_progress(code, relpath, "pra_pc")
            if dry_run:
                report["copiado_pra_pc"] += 1
                continue
            local_path = pc_dir / relpath
            remote_path = f"{android_dir}/{relpath}"
            if adb_mod.pull(remote_path, local_path, serial=serial):
                sys_state[relpath] = {"mtime_pc": local_path.stat().st_mtime, "mtime_android": scan["remote"][relpath]}
                report["copiado_pra_pc"] += 1
            else:
                report["erros"].append(f"pull falhou: {code}/{relpath}")

        if not dry_run:
            for relpath in classified["sem_mudanca"]:
                sys_state[relpath] = {"mtime_pc": scan["local"][relpath], "mtime_android": scan["remote"][relpath]}

    if not dry_run:
        save_state(state)

    return report
