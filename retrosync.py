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
        for label, remote in result["fuzzy"]:
            all_fuzzy.append((code, label, remote))
        REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False))

    if not args.apply:
        print("\n(modo simulação - nada foi baixado, rode com --apply)")

    if all_fuzzy:
        print(f"\n=== {len(all_fuzzy)} casos via FUZZY MATCH (revisar manualmente, não foram aplicados) ===")
        for code, label, remote in all_fuzzy:
            print(f"  [{code}] {label}  ->  {remote}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="retrosync", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="sincroniza saves/metricas/capas PC <-> Android")
    sync.add_argument("scope", choices=["saves", "states", "metrics", "covers", "all"], default="all", nargs="?")
    sync.add_argument("--apply", action="store_true", help="aplica as mudancas (padrao: so mostra)")

    covers = sub.add_parser("fetch-covers", help="busca capas no libretro-thumbnails")
    covers.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    covers.add_argument("--apply", action="store_true")

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
    else:
        raise NotImplementedError(f"comando '{args.command}' ainda nao implementado")


if __name__ == "__main__":
    main()
