#!/usr/bin/env python3
"""
PyRetro - CLI de manutenção do acervo RetroArch (PC <-> Android).

Comandos:
    retrosync sync [saves|states|metrics|covers|all]  [--apply]   (ainda não implementado)
    retrosync fetch-covers <SISTEMA|all> [--apply]
    retrosync fix-cues <pasta|all> [--rename-files] [--apply]     (ainda não implementado)

Todo comando roda em modo de simulação por padrão (mostra o que faria)
e só escreve/copia com --apply. Nenhum comando deleta arquivos. Fuzzy
match de capas nunca é aplicado automaticamente, só reportado.
"""
import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import covers as covers_mod
from core import launchbox as launchbox_mod
from core import sanitize as sanitize_mod

CONFIG_PATH = Path(__file__).parent / "config.toml"
REGISTRY_PATH = Path(__file__).parent / "cache" / "covers_registry.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config.toml não encontrado - copie config.example.toml para {CONFIG_PATH}")
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def cmd_fetch_covers(args) -> None:
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    systems = cfg["systems"]

    targets = list(systems.keys()) if args.system.lower() == "all" else [args.system.upper()]

    registry = json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else {}

    all_fuzzy = []
    for code in targets:
        sysinfo = systems.get(code)
        if not sysinfo:
            print(f"[{code}] sistema desconhecido no config.toml, pulando")
            continue
        result = covers_mod.process_system(
            code, sysinfo["capas"], sysinfo["repo"], capas_root, registry, apply=args.apply
        )
        print(f"{code:9} exato:{result['exact']:4}  fuzzy:{len(result['fuzzy']):4}  "
              f"sem_match:{result['no_match']:4}  ja_registrado:{result['cached']:4}")
        if result["rate_limited"]:
            print(f"          cota da API do GitHub esgotou no meio - parou aqui, "
                  f"os itens restantes ficam pendentes (não foram marcados sem_match)")
        for label, remote in result["fuzzy"]:
            all_fuzzy.append((code, label, remote))
        REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False))

    if not args.apply:
        print("\n(modo simulação - nada foi baixado, rode com --apply)")

    if all_fuzzy:
        print(f"\n=== {len(all_fuzzy)} casos via FUZZY MATCH (revisar manualmente, não foram aplicados) ===")
        for code, label, remote in all_fuzzy:
            print(f"  [{code}] {label}  ->  {remote}")


def cmd_fetch_covers_fallback(args) -> None:
    """Segunda passada, só pros itens que o fetch-covers (libretro-thumbnails)
    já marcou como no_match no registro. Usa o LaunchBox Games DB como
    fonte alternativa (ver core/launchbox.py). Não precisa reprocessar
    tudo de novo - só lê os no_match que já estão registrados."""
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    systems = cfg["systems"]

    targets = list(systems.keys()) if args.system.lower() == "all" else [args.system.upper()]
    targets = [t for t in targets if t in launchbox_mod.PLATFORM_MAP]

    registry = json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else {}
    index = launchbox_mod.build_index(force=args.rebuild_index)

    for code in targets:
        sysinfo = systems.get(code)
        if not sysinfo:
            print(f"[{code}] sistema desconhecido no config.toml, pulando")
            continue
        reg_sys = registry.get(code, {})
        total_no_match = sum(1 for v in reg_sys.values() if v.get("status") == "no_match")

        found = launchbox_mod.process_system_fallback(
            code, sysinfo["capas"], capas_root, registry, index, apply=args.apply
        )

        print(f"{code:9} achado_no_launchbox:{found:4}  (de {total_no_match} sem_match anteriores)")
        REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False))

    if not args.apply:
        print("\n(modo simulação - nada foi baixado, rode com --apply)")


def cmd_convert_covers(args) -> None:
    """RetroArch só exibe thumbnail em PNG (confirmado em 01/08) - .jpg
    fica invisível no menu mesmo com nome certo. Converte tudo pra PNG."""
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    systems = cfg["systems"]
    targets = list(systems.keys()) if args.system.lower() == "all" else [args.system.upper()]

    total = {"convertido": 0, "seria_convertido": 0, "falhou": 0, "png_ja_existe": 0}
    for code in targets:
        sysinfo = systems.get(code)
        if not sysinfo:
            print(f"[{code}] sistema desconhecido no config.toml, pulando")
            continue
        capas_dir = capas_root / sysinfo["capas"] / "Named_Boxarts"
        results = covers_mod.convert_jpg_to_png(capas_dir, apply=args.apply)
        if not results:
            continue
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            total[r["status"]] = total.get(r["status"], 0) + 1
        print(f"{code:9} " + "  ".join(f"{k}:{v}" for k, v in counts.items()))
        for r in results:
            if r["status"] == "falhou":
                print(f"          FALHOU: {r['file']} - {r.get('erro', '')}")

    print(f"\ntotal: " + "  ".join(f"{k}:{v}" for k, v in total.items()))
    if not args.apply:
        print("(modo simulação - nada foi convertido, rode com --apply)")


def cmd_sanitize_names(args) -> None:
    """RetroArch não aceita &, :, * em nome de arquivo. Roda em capas
    E roms juntos (não dá pra sanitizar só um lado sem quebrar o
    casamento entre capa e ROM pelo nome)."""
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()

    roots = []
    if args.target in ("all", "capas"):
        roots.append(("Capas", capas_root))
    if args.target in ("all", "roms"):
        roots.append(("ROMs", roms_root))

    total = {"renomeado": 0, "seria_renomeado": 0, "conflito": 0}
    for label, root in roots:
        results = sanitize_mod.scan_and_rename(root, apply=args.apply)
        if not results:
            print(f"{label}: nada pra renomear")
            continue
        print(f"\n=== {label} ({len(results)}) ===")
        for r in results:
            total[r["status"]] += 1
            old_name = Path(r["old"]).name
            new_name = Path(r["new"]).name
            marker = {"renomeado": "OK", "seria_renomeado": "->", "conflito": "!! CONFLITO"}[r["status"]]
            print(f"  {marker}  {old_name}  ->  {new_name}")

    print(f"\ntotal: renomeado:{total['renomeado']}  seria_renomeado:{total['seria_renomeado']}  "
          f"conflito:{total['conflito']}")
    if total["conflito"]:
        print("(itens em conflito não foram tocados - já existe um arquivo com o nome novo)")
    if not args.apply:
        print("(modo simulação - nada foi renomeado, rode com --apply)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="retrosync", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="sincroniza saves/metricas/capas PC <-> Android")
    sync.add_argument("scope", choices=["saves", "states", "metrics", "covers", "all"], default="all", nargs="?")
    sync.add_argument("--apply", action="store_true", help="aplica as mudancas (padrao: so mostra)")

    covers = sub.add_parser("fetch-covers", help="busca capas no libretro-thumbnails")
    covers.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    covers.add_argument("--apply", action="store_true")

    covers_fb = sub.add_parser(
        "fetch-covers-fallback",
        help="segunda passada nos sem_match do fetch-covers, usando LaunchBox Games DB",
    )
    covers_fb.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    covers_fb.add_argument("--apply", action="store_true")
    covers_fb.add_argument(
        "--rebuild-index", action="store_true",
        help="reprocessa o Metadata.xml do zero (~90s) em vez de usar o cache/launchbox_index.json",
    )

    convert = sub.add_parser("convert-covers", help="converte capas .jpg pra .png (RetroArch so exibe PNG)")
    convert.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    convert.add_argument("--apply", action="store_true")

    sanitize = sub.add_parser("sanitize-names", help="troca & : * por caracteres aceitos pelo RetroArch")
    sanitize.add_argument("target", choices=["capas", "roms", "all"], default="all", nargs="?")
    sanitize.add_argument("--apply", action="store_true")

    cues = sub.add_parser("fix-cues", help="corrige referencias FILE dentro dos .cue")
    cues.add_argument("target", help="pasta de sistema (ex: PS) ou 'all'")
    cues.add_argument("--rename-files", action="store_true", help="tambem renomeia os .bin fisicos")
    cues.add_argument("--apply", action="store_true")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "fetch-covers":
        cmd_fetch_covers(args)
    elif args.command == "fetch-covers-fallback":
        cmd_fetch_covers_fallback(args)
    elif args.command == "convert-covers":
        cmd_convert_covers(args)
    elif args.command == "sanitize-names":
        cmd_sanitize_names(args)
    else:
        raise NotImplementedError(f"comando '{args.command}' ainda nao implementado")


if __name__ == "__main__":
    main()
