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
from core import adb as adb_mod
from core import covers as covers_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import organize as organize_mod
from core import sanitize as sanitize_mod
from core import sync as sync_mod

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

    total = {"convertido": 0, "seria_convertido": 0, "falhou": 0,
              "jpg_orfao_removido": 0, "jpg_orfao_seria_removido": 0}
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


def cmd_validate_covers(args) -> None:
    """Achado em 02/08: capas reais tinham bytes JPEG salvos com nome
    .png (upload manual antigo, ou fonte que não conferia o conteúdo
    real) - RetroArch simplesmente não mostra nada pra elas, sem erro
    visível. Confere pelos primeiros bytes de cada .png, não pela
    extensão."""
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    systems = cfg["systems"]
    targets = list(systems.keys()) if args.system.lower() == "all" else [args.system.upper()]

    total = {"corrigido": 0, "seria_corrigido": 0, "falhou": 0}
    for code in targets:
        sysinfo = systems.get(code)
        if not sysinfo:
            print(f"[{code}] sistema desconhecido no config.toml, pulando")
            continue
        capas_dir = capas_root / sysinfo["capas"] / "Named_Boxarts"
        results = covers_mod.validate_png_content(capas_dir, apply=args.apply)
        if not results:
            continue
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            total[r["status"]] = total.get(r["status"], 0) + 1
        print(f"{code:9} " + "  ".join(f"{k}:{v}" for k, v in counts.items()))
        for r in results:
            print(f"          {r['status']}: {r['file']}" + (f" - {r.get('erro', '')}" if r.get("erro") else ""))

    print(f"\ntotal: " + "  ".join(f"{k}:{v}" for k, v in total.items()))
    if not args.apply:
        print("(modo simulação - nada foi corrigido, rode com --apply)")


def cmd_organize(args) -> None:
    """Só lista o que está esperando em roms_root/<organizar_dir>/ e os
    sistemas candidatos por extensão - mover é feito pela GUI (extensão
    ambígua é comum: .iso/.cue/.chd batem com vários sistemas, decidir
    isso direito pede uma tela, não um comando de linha)."""
    cfg = load_config()
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    staging = cfg["pc"].get("organizar_dir", "0-Organizar")
    ext_index = organize_mod.build_ext_index(cfg["systems"], cfg.get("heavy_systems", {}))
    pending = organize_mod.list_pending(roms_root, staging, ext_index)

    if not pending:
        print(f"nada esperando em roms_root/{staging}/")
        return

    for item in pending:
        gb = item["size"] / (1024 ** 3)
        tag = "PASTA" if item["is_dir"] else "arquivo"
        if not item["candidates"]:
            cand_str = "nenhum sistema reconhece essa extensão" if not item["is_dir"] else "pasta (sem suporte automático ainda)"
        elif len(item["candidates"]) == 1:
            cand_str = item["candidates"][0]["code"]
        else:
            cand_str = "AMBIGUO: " + ", ".join(c["code"] for c in item["candidates"])
        print(f"  [{tag:7}] {item['name']:55} {gb:6.2f} GB   -> {cand_str}")

    print(f"\ntotal: {len(pending)} item(ns). Mover é feito pela GUI (botão 🗂 Organizar).")


def cmd_heavy_roms(args) -> None:
    """Lista (e opcionalmente envia/baixa) ROMs de consoles pesados -
    esses não sincronizam sozinhos via Google Drive como os sistemas
    leves, então o envio/download é sob demanda, um item de cada vez."""
    cfg = load_config()
    heavy = heavy_mod.load_heavy_systems(cfg)
    code = args.system.upper()
    sysinfo = heavy.get(code)
    if not sysinfo:
        sys.exit(f"sistema pesado desconhecido: '{code}' - opções: {', '.join(sorted(heavy)) or '(nenhum configurado)'}")

    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    jogos_root = cfg["android"]["jogos_root"]
    serial = cfg["android"].get("device_serial") or None

    local_items = heavy_mod.list_local(code, roms_root, sysinfo.get("exts", []))
    local_by_name = {i["name"]: i for i in local_items}
    drive_items = heavy_mod.list_drive_items(code, cfg)
    drive_by_name = {i["name"]: i for i in drive_items}

    all_names = sorted(set(local_by_name) | set(drive_by_name))
    if not all_names:
        print(f"nenhum item em roms_root/{code}/ nem no Drive")
        return

    android_ok = False
    remote_names = set()
    try:
        serial = adb_mod.ensure_connected(serial)
        remote_names = heavy_mod.list_remote_names(code, jogos_root, serial)
        android_ok = True
    except adb_mod.AdbError as e:
        print(f"(celular indisponível: {e})")

    if args.send:
        if not android_ok:
            sys.exit("celular não conectado - não dá pra enviar agora")
        if args.send not in local_by_name:
            sys.exit(f"'{args.send}' não encontrado no PC (roms_root/{code}/) - baixe do Drive primeiro com --download")
        print(f"enviando '{args.send}'... (pode demorar - arquivos grandes)")
        ok, msg = heavy_mod.send_to_phone(
            code, args.send, roms_root, jogos_root, serial, sysinfo.get("exts", []), overwrite=args.overwrite,
        )
        print(("OK: " if ok else "FALHOU: ") + msg)
        return

    if args.download:
        if args.download not in drive_by_name:
            sys.exit(f"'{args.download}' não encontrado no Drive (rclone drive:{{drive_roms_root}}/{code}/)")
        print(f"baixando '{args.download}' do Drive... (pode demorar - arquivos grandes)")
        ok, msg = heavy_mod.download_from_drive(code, args.download, roms_root, cfg)
        print(("OK: " if ok else "FALHOU: ") + msg)
        return

    print(f"{code} ({sysinfo.get('nome', code)}):")
    for name in all_names:
        local = local_by_name.get(name)
        drive = drive_by_name.get(name)
        size = local["size"] if local else drive["size"]
        is_dir = local["is_dir"] if local else drive["is_dir"]
        gb = size / (1024 ** 3)
        tag = "PASTA" if is_dir else "arquivo"
        flags = []
        if local:
            flags.append("no celular" if name in remote_names else "só no PC")
        else:
            flags.append("só no Drive - use --download")
        print(f"  [{tag:7}] {name:55} {gb:6.2f} GB   [{', '.join(flags)}]")
    if not android_ok:
        print("\n(celular desconectado - status \"no celular\" não pôde ser conferido)")


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


def cmd_sync(args) -> None:
    """Por enquanto só 'covers' está implementado - saves/states/metrics
    seguem a mesma arquitetura (ver core/sync.py) mas ainda não foram
    escritos."""
    cfg = load_config()
    if args.scope not in ("covers", "all"):
        sys.exit(f"sync '{args.scope}' ainda não implementado - só 'covers' por enquanto")

    try:
        report = sync_mod.sync_capas(cfg, dry_run=not args.apply)
    except adb_mod.AdbError as e:
        sys.exit(f"erro de adb: {e}")

    print(f"capas: pro_android:{report['copiado_pro_android']:4}  pra_pc:{report['copiado_pra_pc']:4}  "
          f"sem_mudanca:{report['sem_mudanca']:4}  conflitos:{len(report['conflitos']):4}")

    if report["conflitos"]:
        print("\n=== CONFLITOS (mudou dos dois lados desde a ultima sync - revisar na mao) ===")
        for c in report["conflitos"]:
            print(f"  {c}")
    if report["erros"]:
        print("\n=== ERROS ===")
        for e in report["erros"]:
            print(f"  {e}")
    if not args.apply:
        print("\n(modo simulacao - nada foi copiado, rode com --apply)")


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

    validate = sub.add_parser(
        "validate-covers",
        help="confere se os .png de capa sao PNG de verdade (pelo conteudo, nao pela extensao)",
    )
    validate.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    validate.add_argument("--apply", action="store_true")

    sub.add_parser(
        "organize",
        help="lista ROMs esperando organização em roms_root/<organizar_dir>/ (mover é feito pela GUI)",
    )

    heavy = sub.add_parser(
        "heavy-roms",
        help="lista/envia ROMs de consoles pesados (PS, SDC, PS2, GameCube, Wii, PSP, 3DS)",
    )
    heavy.add_argument("system", help="codigo do sistema pesado (ex: PS2)")
    heavy.add_argument("--send", metavar="NOME", help="manda esse item (arquivo ou pasta) pro celular")
    heavy.add_argument("--download", metavar="NOME", help="baixa esse item do Google Drive pro PC (via rclone)")
    heavy.add_argument("--overwrite", action="store_true", help="sobrescreve se ja existir no celular")

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
    if args.command == "sync":
        cmd_sync(args)
    elif args.command == "fetch-covers":
        cmd_fetch_covers(args)
    elif args.command == "fetch-covers-fallback":
        cmd_fetch_covers_fallback(args)
    elif args.command == "convert-covers":
        cmd_convert_covers(args)
    elif args.command == "validate-covers":
        cmd_validate_covers(args)
    elif args.command == "organize":
        cmd_organize(args)
    elif args.command == "heavy-roms":
        cmd_heavy_roms(args)
    elif args.command == "sanitize-names":
        cmd_sanitize_names(args)
    else:
        raise NotImplementedError(f"comando '{args.command}' ainda nao implementado")


if __name__ == "__main__":
    main()
