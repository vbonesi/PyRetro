#!/usr/bin/env python3
"""
PyRetro - CLI de manutenção do acervo RetroArch (PC <-> Android).

Comandos:
    retrosync sync [saves|states|metrics|covers|all]  [--apply]   (ainda não implementado)
    retrosync backup-saves [--apply]
    retrosync backup-config [pc|android|all] [--apply]
    retrosync rebuild-playlist <SISTEMA> [pc|android|all] [--apply]
    retrosync fetch-covers <SISTEMA|all> [--apply]
    retrosync fetch-covers-cloud <SISTEMA|all> [--apply]
    retrosync fix-cues <pasta|all> [--rename-files] [--apply]     (ainda não implementado)
    retrosync heavy-catalog [--apply]
    retrosync sortear [SISTEMA]
    retrosync library-import-sheet <CSV> [--apply]
    retrosync library-refresh heroic [--apply]

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
from core import config_backup as config_backup_mod
from core import covers as covers_mod
from core import emu_sync as emu_sync_mod
from core import heavy_roms as heavy_mod
from core import launchbox as launchbox_mod
from core import library as library_mod
from core import organize as organize_mod
from core import pc_backup as pc_backup_mod
from core import playlist as playlist_mod
from core import sanitize as sanitize_mod
from core import sortear as sortear_mod
from core import sync as sync_mod

CONFIG_PATH = Path(__file__).parent / "config.toml"
REGISTRY_PATH = Path(__file__).parent / "cache" / "covers_registry.json"
HEAVY_CATALOG_PATH = Path(__file__).parent / "cache" / "heavy_catalog.json"


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


def cmd_fetch_covers_cloud(args) -> None:
    """Mesma busca/match de fetch-covers (libretro-thumbnails, exato
    baixa, fuzzy só no relatorio) - a diferenca e de onde vem a lista
    de jogos: aqui e o catalogo completo no Google Drive (via rclone,
    core/heavy_roms.list_drive_items), nao uma varredura de roms_root
    local. Pra sistema onde a nuvem tem muito mais jogo do que o que
    ja foi baixado pro PC - nao baixa ROM nenhuma, so a capa. Depois
    de rodar isso, "fetch-covers-fallback <SISTEMA>" funciona
    normalmente em cima do que sobrou sem match (le do registry, nao
    de arquivo local).

    "all" só cobre [systems] (leve) - sistema pesado (PS/PS2/GameCube/
    Wii/PSP/3DS) precisa ser pedido pelo código explicitamente (ex:
    "PS2"), pra "all" não ficar lento à toa cada vez que só se quer
    atualizar os leves (list_drive_items pode levar ~90s por sistema
    pesado, ver core/heavy_roms.py). Capa de pesado é só pra EXIBIÇÃO
    (Biblioteca/galeria) - não afeta send/download de ROM (core/
    heavy_roms.py), que continua sob demanda igual sempre foi."""
    cfg = load_config()
    capas_root = Path(cfg["pc"]["capas_root"]).expanduser()
    systems = cfg["systems"]
    heavy = heavy_mod.load_heavy_systems(cfg)
    targets = list(systems.keys()) if args.system.lower() == "all" else [args.system.upper()]

    registry = json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else {}

    all_fuzzy = []
    for code in targets:
        sysinfo = systems.get(code) or heavy.get(code)
        if not sysinfo:
            print(f"[{code}] sistema desconhecido no config.toml, pulando")
            continue
        if code in covers_mod.COVERS_EXCLUDED:
            print(f"[{code}] esta em COVERS_EXCLUDED (core/covers.py), pulando")
            continue

        exts_lower = {e.lower().lstrip(".") for e in sysinfo.get("exts", [])}
        cloud_items = heavy_mod.list_drive_items(code, cfg)
        cloud_labels = sorted({
            Path(i["name"]).stem for i in cloud_items
            if not i["is_dir"] and Path(i["name"]).suffix.lower().lstrip(".") in exts_lower
        })
        if not cloud_labels:
            print(f"{code:9} nada no Drive (rclone drive:{{drive_roms_root}}/{code}/) com essas extensoes")
            continue

        result = covers_mod.process_system_cloud(
            code, sysinfo["capas"], sysinfo["repo"], capas_root, cloud_labels, registry, apply=args.apply
        )
        print(f"{code:9} nuvem:{len(cloud_labels):4}  exato:{result['exact']:4}  fuzzy:{len(result['fuzzy']):4}  "
              f"sem_match:{result['no_match']:4}  ja_registrado:{result['cached']:4}")
        if result["rate_limited"]:
            print(f"          cota da API do GitHub esgotou no meio - parou aqui, "
                  f"os itens restantes ficam pendentes (não foram marcados sem_match)")
        for label, remote in result["fuzzy"]:
            all_fuzzy.append((code, label, remote))
        REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False))

    if not args.apply:
        print("\n(modo simulacao - nada foi baixado, rode com --apply)")

    if all_fuzzy:
        print(f"\n=== {len(all_fuzzy)} casos via FUZZY MATCH (revisar manualmente, não foram aplicados) ===")
        for code, label, remote in all_fuzzy:
            print(f"  [{code}] {label}  ->  {remote}")


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


def cmd_heavy_catalog(args) -> None:
    """Atualiza cache/heavy_catalog.json com o catálogo completo (via
    rclone) de cada sistema pesado - é o que permite o comando
    `sortear` incluir jogos que ainda nem foram baixados pro PC (ver
    core/sortear.py). Pode demorar - até ~90s por sistema pesado
    configurado, mesma limitação de heavy_roms.list_drive_items."""
    cfg = load_config()
    print("consultando o Google Drive (pode demorar - ~90s por sistema)...")
    catalog = sortear_mod.refresh_heavy_catalog(cfg)
    for code, names in catalog.items():
        print(f"  {code:6} {len(names)} jogo(s)")
    total = sum(len(n) for n in catalog.values())

    if args.apply:
        sortear_mod.save_heavy_catalog(HEAVY_CATALOG_PATH, catalog)
        print(f"\ncatálogo salvo em {HEAVY_CATALOG_PATH} ({total} jogo(s) no total)")
    else:
        print(f"\ntotal: {total} jogo(s) (modo simulação - nada foi salvo, rode com --apply)")


def cmd_sortear(args) -> None:
    """Sorteia um jogo aleatório da coleção - leve (roms_root, sempre
    local) e pesado (a partir do catálogo cacheado por
    `heavy-catalog`). Sem argumento, sorteia entre tudo; com um código
    de sistema (leve ou pesado), restringe o sorteio a ele."""
    cfg = load_config()
    roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
    catalog = sortear_mod.load_heavy_catalog(HEAVY_CATALOG_PATH)

    try:
        pool = sortear_mod.build_pool(cfg, roms_root, catalog, args.system)
    except ValueError:
        sys.exit(f"sistema desconhecido: '{args.system.upper()}'")

    if not args.system and not catalog:
        print("(aviso: catálogo de pesados vazio ou nunca atualizado - rode "
              "'retrosync heavy-catalog --apply' pra incluir PS/PS2/etc no sorteio)\n")

    if not pool:
        alvo = f" em '{args.system.upper()}'" if args.system else ""
        sys.exit(f"nenhum jogo encontrado pra sortear{alvo}")

    code, name, kind = sortear_mod.draw(pool)
    heavy = heavy_mod.load_heavy_systems(cfg)
    label = cfg["systems"][code]["capas"] if kind == "leve" else heavy[code].get("nome", code)

    print(f"sorteado: {name}")
    print(f"sistema:  {code} - {label} ({kind}, {len(pool)} jogo(s) no pool)")

    if kind == "pesado":
        sysinfo = heavy[code]
        local_names = {i["name"] for i in heavy_mod.list_local(code, roms_root, sysinfo.get("exts", []))}
        if name in local_names:
            print("já está no PC")
        else:
            print(f"só no Drive - baixe com: retrosync heavy-roms {code} --download \"{name}\"")


def cmd_library_import_sheet(args) -> None:
    """Importa o CSV exportado da planilha de acompanhamento (Google
    Sheets: Arquivo > Fazer download > CSV) pra dentro de
    library_root/library.json. Pensado pra rodar mais de uma vez -
    upsert por nome+plataforma (core/library.py), então rodar de novo
    com um CSV atualizado não duplica, só atualiza quem já existe."""
    cfg = load_config()
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)

    csv_path = Path(args.csv).expanduser()
    if not csv_path.exists():
        sys.exit(f"CSV não encontrado: {csv_path}")

    result = library_mod.import_sheet_csv(library, csv_path)
    print(f"novo(s): {result['added']}  atualizado(s): {result['updated']}")

    if args.apply:
        library_mod.save_library(library_path, library)
        print(f"\nsalvo em {library_path} ({len(library['games'])} jogo(s) no total)")
    else:
        print("\n(modo simulação - nada foi salvo, rode com --apply)")


def cmd_library_refresh(args) -> None:
    """Cruza library_root/library.json com jogos possuídos em outra
    fonte:
    - 'heroic' - Epic/GOG/Amazon via cache local do Heroic Games
      Launcher, sem tocar rede (core/library.read_heroic_libraries).
    - 'steam' - API Web oficial, precisa de [steam] api_key+steamid64.
    - 'switch' - lê roms_root/NSW/ (nome da pasta, tag [NSP]/[NSZ]
      removida) - sem gestão de arquivo, só confirma posse e cruza
      nota/observações já existentes na planilha por nome.
    - 'psn' - troféus da PSN (só jogo já aberto ao menos 1x), precisa
      de [psn] npsso (token manual, válido ~2 meses).
    - 'xbox' - OpenXBL (não-oficial), precisa de [xbox] api_key."""
    cfg = load_config()
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)

    if args.source == "heroic":
        heroic_cfg = cfg.get("heroic", {})
        owned = library_mod.read_heroic_libraries(heroic_cfg)
        if not owned:
            config_dir = heroic_cfg.get("config_dir") or "~/.config/heroic"
            sys.exit(f"nada encontrado em {config_dir}/store_cache/ - Heroic instalado "
                      f"e com pelo menos uma loja logada?")
        fonte_label = "heroic: {n} jogo(s) possuído(s) no total (Epic+GOG+Amazon)"
    elif args.source == "steam":
        try:
            owned = library_mod.read_steam_library(cfg.get("steam", {}))
        except (ValueError, RuntimeError) as e:
            sys.exit(str(e))
        fonte_label = "steam: {n} jogo(s) possuído(s)"
    elif args.source == "switch":
        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
        owned = library_mod.read_switch_library(roms_root, cfg)
        if not owned:
            sys.exit(f"nada encontrado em {roms_root / 'NSW'}")
        fonte_label = "switch: {n} jogo(s) em roms_root/NSW/"
    elif args.source == "psn":
        try:
            owned = library_mod.read_psn_library(cfg.get("psn", {}))
        except (ValueError, RuntimeError) as e:
            sys.exit(str(e))
        fonte_label = "psn: {n} jogo(s) na biblioteca (compras PS4/PS5)"
    elif args.source == "xbox":
        try:
            owned = library_mod.read_xbox_library(cfg.get("xbox", {}))
        except (ValueError, RuntimeError) as e:
            sys.exit(str(e))
        fonte_label = "xbox: {n} jogo(s) jogado(s) (histórico, NÃO é biblioteca - mistura Game Pass/comprado/disco antigo)"
    else:
        sys.exit(f"fonte '{args.source}' ainda não implementada")

    result = library_mod.merge_owned(library, owned)
    print(fonte_label.format(n=len(owned)))
    print(f"  novo(s): {result['added']}   já rastreado(s): {result['merged']}")
    if result["possible_dupes"]:
        print(f"\n=== {len(result['possible_dupes'])} possível(is) duplicata(s) "
              f"(revisar na mão, NÃO foi mesclado) ===")
        for owned_name, existing_name in result["possible_dupes"]:
            print(f"  '{owned_name}'  ~  '{existing_name}'")

    if args.apply:
        library_mod.save_library(library_path, library)
        print(f"\nsalvo em {library_path} ({len(library['games'])} jogo(s) no total)")
    else:
        print("\n(modo simulação - nada foi salvo, rode com --apply)")


def cmd_library_add(args) -> None:
    """Cadastro manual de jogos possuídos - pra fonte sem API confiável
    (PSN/Xbox, decisão do usuário em 27/08: ver docs/changelog.md) ou
    qualquer lista avulsa. Arquivo texto, um jogo por linha. Mesmo merge
    seguro de library-refresh (nome exato -> anota fonte no jogo que já
    existe; sem bater -> registro novo; parecido demais -> só
    relatório, nunca mesclado sozinho)."""
    cfg = load_config()
    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)

    txt_path = Path(args.arquivo).expanduser()
    if not txt_path.exists():
        sys.exit(f"arquivo não encontrado: {txt_path}")

    owned = library_mod.read_manual_list(txt_path, args.plataforma, args.fonte)
    if not owned:
        sys.exit("arquivo vazio (ou só tinha linha em branco/comentário)")

    result = library_mod.merge_owned(library, owned)
    print(f"{args.fonte} ({args.plataforma}): {len(owned)} jogo(s) na lista")
    print(f"  novo(s): {result['added']}   já rastreado(s): {result['merged']}")
    if result["possible_dupes"]:
        print(f"\n=== {len(result['possible_dupes'])} possível(is) duplicata(s) (revisar na mão, NÃO foi mesclado) ===")
        for a, b in result["possible_dupes"]:
            print(f"  '{a}'  ~  '{b}'")

    if args.apply:
        library_mod.save_library(library_path, library)
        print(f"\nsalvo em {library_path} ({len(library['games'])} jogo(s) no total)")
    else:
        print("\n(modo simulação - nada foi salvo, rode com --apply)")


def cmd_library_fetch_covers(args) -> None:
    """Busca capa (SteamGridDB) pra todo jogo da biblioteca que ainda
    não tem `capa` - salva em library_root/capas/<id>.png. Precisa de
    [steamgriddb] api_key no config.toml (grátis, steamgriddb.com >
    Preferences > API). Match exato só (nome normalizado igual ao 1º
    resultado da busca) - sem match vira só um contador, não trava nem
    lista tudo (potencialmente centenas)."""
    cfg = load_config()
    api_key = cfg.get("steamgriddb", {}).get("api_key")
    if not api_key:
        sys.exit("faltando api_key em [steamgriddb] no config.toml")

    library_root = Path(cfg["pc"]["library_root"]).expanduser()
    library_path = library_root / "library.json"
    library = library_mod.load_library(library_path)
    capas_dir = library_root / "capas"

    pending = sum(1 for g in library["games"] if not g["capa"] and not g.get("oculto"))
    if pending == 0:
        print("todo jogo já tem capa (ou a biblioteca está vazia)")
        return
    print(f"{pending} jogo(s) sem capa")

    if not args.apply:
        print("(modo simulação - rode com --apply pra baixar de verdade)")
        return

    # Capa oficial da Steam primeiro (ver core/library.fetch_covers),
    # SteamGridDB pro resto.
    steam_appids = library_mod.steam_appid_index(cfg.get("steam", {}))
    print(f"{len(steam_appids)} jogo(s) da Steam com capa oficial disponível")
    print("buscando (pode demorar)...")

    # Salva a cada 20 jogos, não só no final - são 2 chamadas de rede
    # por jogo, um lote de centenas demora minutos, e sem isso um
    # Ctrl+C ou erro no meio perde a marcação de TUDO que já foi
    # baixado até ali (os arquivos .png ficam no disco de qualquer
    # jeito, mas sem o campo "capa" gravado o próximo run baixa de
    # novo à toa).
    counter = {"n": 0}

    def on_progress(nome, status):
        counter["n"] += 1
        if counter["n"] % 20 == 0:
            library_mod.save_library(library_path, library)

    result = library_mod.fetch_covers(library, capas_dir, api_key, on_progress=on_progress,
                                      steam_appids=steam_appids, cfg=cfg)
    library_mod.save_library(library_path, library)
    print(f"baixado(s): {result['baixado']} ({result['via_steam']} Steam, {result['via_ss']} ScreenScraper)   "
          f"sem_match: {result['sem_match']}   erro: {result['erro']}")

    # Capa achada por um título DIFERENTE do que está no registro (selo
    # de relançamento removido, ver nomes_alternativos_de_capa) - é o
    # lote que mais merece conferida de olho, então sai nominalmente.
    if result.get("aliases"):
        print(f"\n{len(result['aliases'])} capa(s) vieram de uma busca pelo título sem o selo "
              f"(confira estas):")
        for nome, buscado in result["aliases"]:
            print(f"  {nome}  ->  buscado como {buscado!r}")


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


def cmd_backup_saves(args) -> None:
    """PC -> Drive, uma direção só. A maioria dos emuladores já escreve
    direto dentro de Saves/ (o Drive faz o backup sozinho); isso aqui
    cobre só o que sobra (Dolphin GC/Wii) - ver core/pc_backup.py."""
    cfg = load_config()
    items = pc_backup_mod.plan(cfg)
    if not items:
        print("nada pra fazer backup (tudo já copiado, ou dolphin_data_root vazio em config.toml)")
        return

    by_source = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)
    for source, group in by_source.items():
        print(f"\n=== {source} ({len(group)}) ===")
        for item in group:
            print(f"  [{item['action']:10}] {item['rel_path']}")

    if args.apply:
        pc_backup_mod.apply(items)
        print(f"\ncopiado: {len(items)} arquivo(s)")
    else:
        print(f"\ntotal: {len(items)} arquivo(s) (modo simulacao - nada foi copiado, rode com --apply)")


def cmd_backup_config(args) -> None:
    """Snapshot datado de retroarch.cfg + config/ + playlists/ pro PC
    e/ou celular, pasta nova a cada rodada
    (Backups/retroarch_<pc|android>_<data>/) - ver core/config_backup.py."""
    cfg = load_config()
    backups_root = Path(cfg["pc"]["backups_root"]).expanduser()
    targets = ["pc", "android"] if args.target == "all" else [args.target]

    if "pc" in targets:
        plan = config_backup_mod.backup_pc(cfg, backups_root, apply=args.apply)
        print(f"[PC] -> {plan['dest']}")
        for label, src in (("retroarch.cfg", plan["cfg_src"]), ("config/", plan["config_src"]),
                           ("playlists/", plan["playlists_src"])):
            print(f"  {label:14} {'ok' if src.exists() else 'NAO ENCONTRADO'}  ({src})")
        if args.apply:
            for k, v in plan["counts"].items():
                print(f"  -> {k}: {v} arquivo(s) copiado(s)")

    if "android" in targets:
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            print(f"[Android] erro de adb: {e}")
            serial = None
        if serial:
            plan = config_backup_mod.backup_android(cfg, backups_root, serial, apply=args.apply)
            print(f"[Android] -> {plan['dest']}")
            print(f"  retroarch.cfg  ({plan['cfg_src']})")
            print(f"  config/        ({plan['config_src']})")
            print(f"  playlists/     ({plan['playlists_src']})")
            if args.apply:
                for k, v in plan["counts"].items():
                    ok = plan["ok"][k]
                    print(f"  -> {k}: {v} arquivo(s) copiado(s)" + ("" if ok else "  FALHOU"))

    if not args.apply:
        print("\n(modo simulacao - nada foi copiado, rode com --apply)")


def cmd_rebuild_playlist(args) -> None:
    """Monta playlist .lpl do RetroArch a partir do que existe DE
    VERDADE em roms_root/<CODE>/ (PC) e/ou no celular (Android, via
    adb) - sistemas pesados (PS2/GameCube/Wii/...) não sincronizam sozinhos,
    então PC e Android costumam ter jogos DIFERENTES na mesma pasta; a
    playlist de cada lado reflete só o que aquele lado realmente tem
    (ver core/playlist.py)."""
    cfg = load_config()
    code = args.system.upper()
    sysinfo = cfg["systems"].get(code)
    if not sysinfo:
        sys.exit(f"sistema desconhecido em [systems] no config.toml: '{code}'")
    db_name = f"{sysinfo['capas']}.lpl"
    exts = sysinfo.get("exts", [])
    targets = ["pc", "android"] if args.target == "all" else [args.target]

    if "pc" in targets:
        roms_root = Path(cfg["pc"]["roms_root"]).expanduser()
        content_dir = roms_root / code
        dest = Path(cfg["pc"]["retroarch_root"]).expanduser() / "playlists" / db_name
        names = playlist_mod.list_local_names(code, roms_root, exts)
        if not names:
            print(f"[PC] nada em {content_dir} com extensao {exts} - nada a fazer")
        else:
            print(f"[PC] {dest}")
            for n in names:
                print(f"  {n}")
            if args.apply:
                items = [(str(content_dir / n), Path(n).stem) for n in names]
                pl = playlist_mod.make_playlist(items, str(content_dir), exts, db_name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(pl, indent=1, ensure_ascii=False))
                print(f"  -> gravado ({len(names)} jogo(s))")

    if "android" in targets:
        jogos_root = cfg["android"]["jogos_root"]
        remote_content_dir = f"{jogos_root.rstrip('/')}/{code}"
        remote_dest = f"{cfg['android']['retroarch_root'].rstrip('/')}/playlists/{db_name}"
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            sys.exit(f"erro de adb: {e}")
        names = playlist_mod.list_remote_names(code, jogos_root, exts, serial)
        if not names:
            print(f"[Android] nada em {remote_content_dir} com extensao {exts} - nada a fazer")
        else:
            print(f"[Android] {remote_dest}")
            for n in names:
                print(f"  {n}")
            if args.apply:
                items = [(f"{remote_content_dir}/{n}", Path(n).stem) for n in names]
                pl = playlist_mod.make_playlist(items, remote_content_dir, exts, db_name)
                tmp_dir = Path(__file__).parent / "cache" / "playlists_tmp"
                ok = playlist_mod.push_playlist(pl, remote_dest, serial, tmp_dir)
                print(f"  -> {'enviado' if ok else 'FALHOU'} ({len(names)} jogo(s))")

    if not args.apply:
        print("\n(modo simulacao - nada foi escrito, rode com --apply)")


def cmd_emu_sync(args) -> None:
    """PC <-> Drive <-> Android, mais recente vence, pros saves que
    moram dentro da sandbox do próprio emulador (Dolphin GC/Wii nos
    dois lados; PS2 só a perna Android, já que o PCSX2 do PC escreve
    direto em Drive) - ver core/emu_sync.py.

    Rodando dentro do Termux (docs/termux_setup.md), detecta sozinho e
    muda pra local_mode: sem adb, sem perna PC, a pasta do emulador no
    Android é lida direto (precisa da permissão "Acesso a todos os
    arquivos" concedida ao Termux)."""
    cfg = load_config()
    sources = list(emu_sync_mod.SOURCES) if args.source == "all" else [args.source]
    local_mode = emu_sync_mod.running_in_termux()
    serial = None
    if not local_mode:
        try:
            serial = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
        except adb_mod.AdbError as e:
            sys.exit(f"erro de adb: {e}")

    all_actions, all_conflicts = [], []
    for source in sources:
        result = emu_sync_mod.plan(source, cfg, serial=serial, local_mode=local_mode)
        all_actions += result["actions"]
        all_conflicts += result["conflicts"]

    if not all_actions and not all_conflicts:
        print("nada pra sincronizar (tudo já igual nas tres pontas)")
        return

    by_source = {}
    for a in all_actions:
        by_source.setdefault(a["source"], []).append(a)
    for source, group in by_source.items():
        print(f"\n=== {emu_sync_mod.SOURCES[source]['nome']} ({len(group)}) ===")
        for a in group:
            print(f"  [{a['direction']:16}] {a['rel_path']}")

    if all_conflicts:
        print("\n=== CONFLITOS (PC e Android mudaram os dois desde a ultima sync - revisar na mao) ===")
        for c in all_conflicts:
            print(f"  {c['source']}: {c['rel_path']} (pc={c['pc_mtime']}, android={c['android_mtime']})")

    if args.apply:
        results = emu_sync_mod.apply(all_actions, cfg, serial=serial, local_mode=local_mode)
        erros = [r for r in results if not r["ok"]]
        print(f"\naplicado: {len(results) - len(erros)}/{len(results)}")
        for r in erros:
            print(f"  erro: {r['source']}/{r['rel_path']}: {r['erro']}")
    else:
        print(f"\ntotal: {len(all_actions)} acao(oes) (modo simulacao - nada foi copiado, rode com --apply)")


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

    backup = sub.add_parser(
        "backup-saves",
        help="copia PC -> Drive os saves que nao escrevem direto em Saves/ (Dolphin GC/Wii)",
    )
    backup.add_argument("--apply", action="store_true", help="aplica a copia (padrao: so mostra)")

    backup_cfg = sub.add_parser(
        "backup-config",
        help="snapshot datado de retroarch.cfg + config/ + playlists/ pro PC e/ou celular "
             "(Backups/retroarch_<pc|android>_<data>/)",
    )
    backup_cfg.add_argument("target", choices=["pc", "android", "all"], default="all", nargs="?")
    backup_cfg.add_argument("--apply", action="store_true", help="grava de verdade (padrao: so mostra)")

    rebuild = sub.add_parser(
        "rebuild-playlist",
        help="monta playlist .lpl do RetroArch a partir do que existe em roms_root/<CODE> (PC) e/ou no celular",
    )
    rebuild.add_argument("system", help="codigo do sistema (ex: SS, SDC) - precisa estar em [systems] no config.toml")
    rebuild.add_argument("target", choices=["pc", "android", "all"], default="all", nargs="?")
    rebuild.add_argument("--apply", action="store_true", help="grava/envia de verdade (padrao: so mostra)")

    emu_sync = sub.add_parser(
        "emu-sync",
        help="PC <-> Drive <-> Android, mais recente vence (Dolphin GC/Wii, PS2 memcards/savestates)",
    )
    emu_sync.add_argument("source", choices=list(emu_sync_mod.SOURCES) + ["all"], default="all", nargs="?")
    emu_sync.add_argument("--apply", action="store_true", help="aplica a sincronizacao (padrao: so mostra)")

    covers = sub.add_parser("fetch-covers", help="busca capas no libretro-thumbnails")
    covers.add_argument("system", help="codigo do sistema (ex: SFC) ou 'all'")
    covers.add_argument("--apply", action="store_true")

    covers_cloud = sub.add_parser(
        "fetch-covers-cloud",
        help="busca capas no libretro-thumbnails a partir do catalogo completo no Google Drive (rclone), "
             "nao so do que ja foi baixado pro PC",
    )
    covers_cloud.add_argument("system", help="codigo do sistema (ex: SS) ou 'all'")
    covers_cloud.add_argument("--apply", action="store_true")

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
        help="lista/envia ROMs de consoles pesados (PS, PS2, GameCube, Wii, PSP, 3DS)",
    )
    heavy.add_argument("system", help="codigo do sistema pesado (ex: PS2)")
    heavy.add_argument("--send", metavar="NOME", help="manda esse item (arquivo ou pasta) pro celular")
    heavy.add_argument("--download", metavar="NOME", help="baixa esse item do Google Drive pro PC (via rclone)")
    heavy.add_argument("--overwrite", action="store_true", help="sobrescreve se ja existir no celular")

    heavy_catalog = sub.add_parser(
        "heavy-catalog",
        help="atualiza o cache com o catalogo completo de jogos pesados no Google Drive (usado pelo sortear)",
    )
    heavy_catalog.add_argument("--apply", action="store_true")

    sortear = sub.add_parser(
        "sortear",
        help="sorteia um jogo aleatorio da colecao (roms_root + catalogo de pesados)",
    )
    sortear.add_argument(
        "system", nargs="?",
        help="codigo do sistema (leve ou pesado) pra restringir o sorteio - se omitido, sorteia de tudo",
    )

    lib_import = sub.add_parser(
        "library-import-sheet",
        help="importa o CSV da planilha de acompanhamento pra library.json (upsert por nome+plataforma)",
    )
    lib_import.add_argument("csv", help="caminho do CSV exportado (Google Sheets: Arquivo > Fazer download > CSV)")
    lib_import.add_argument("--apply", action="store_true")

    lib_refresh = sub.add_parser(
        "library-refresh",
        help="cruza a biblioteca com jogos possuidos em outra fonte (heroic = Epic/GOG/Amazon)",
    )
    lib_refresh.add_argument("source", choices=["heroic", "steam", "switch", "psn", "xbox"], help="fonte a consultar")

    lib_add = sub.add_parser(
        "library-add",
        help="cadastro manual de jogos possuidos a partir de um arquivo texto (um nome por linha)",
    )
    lib_add.add_argument("arquivo", help="arquivo texto, um nome de jogo por linha")
    lib_add.add_argument("--plataforma", required=True, help="plataforma a registrar (ex: Xbox, 'PSN (PS4)')")
    lib_add.add_argument("--fonte", required=True, help="tag de fonte a registrar (ex: xbox, psn, psn:fisico)")
    lib_add.add_argument("--apply", action="store_true")

    lib_covers = sub.add_parser(
        "library-fetch-covers",
        help="busca capa (SteamGridDB) pra jogo da biblioteca que ainda nao tem",
    )
    lib_covers.add_argument("--apply", action="store_true")
    lib_refresh.add_argument("--apply", action="store_true")

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
    elif args.command == "backup-saves":
        cmd_backup_saves(args)
    elif args.command == "backup-config":
        cmd_backup_config(args)
    elif args.command == "rebuild-playlist":
        cmd_rebuild_playlist(args)
    elif args.command == "emu-sync":
        cmd_emu_sync(args)
    elif args.command == "fetch-covers":
        cmd_fetch_covers(args)
    elif args.command == "fetch-covers-cloud":
        cmd_fetch_covers_cloud(args)
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
    elif args.command == "heavy-catalog":
        cmd_heavy_catalog(args)
    elif args.command == "sortear":
        cmd_sortear(args)
    elif args.command == "library-import-sheet":
        cmd_library_import_sheet(args)
    elif args.command == "library-refresh":
        cmd_library_refresh(args)
    elif args.command == "library-add":
        cmd_library_add(args)
    elif args.command == "library-fetch-covers":
        cmd_library_fetch_covers(args)
    elif args.command == "sanitize-names":
        cmd_sanitize_names(args)
    else:
        raise NotImplementedError(f"comando '{args.command}' ainda nao implementado")


if __name__ == "__main__":
    main()
