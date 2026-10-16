"""
Mostra as capas do PyRetro (Capas/<sistema>/Named_Boxarts/<nome-da-ROM>.png)
dentro do ES-DE e dos emuladores, sem copiar nada: tudo vira symlink para a
pasta de capas, então uma capa nova ou trocada no PyRetro aparece sozinha.

  ES-DE        downloaded_media/<sistema>/covers -> a pasta Named_Boxarts inteira
  DuckStation  covers/<nome-da-ROM>.<ext>        (um link por ROM que existe)
  PCSX2        covers/<nome-da-ROM>.<ext>        (idem; convive com as capas que
               o próprio PCSX2 baixou, nomeadas pelo serial)
  Dolphin      cache/GameCovers/<ID DE 6 LETRAS>.png (o ID vem do cabeçalho da ROM;
               só .iso e .wbfs - os outros formatos ficam de fora e são avisados)

Nada existente é sobrescrito: um destino que já tem conteúdo de outra origem é
pulado e aparece como "pulado" no relatório."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

HOME = Path.home()
ESDE_HOME = HOME / ".local/share/bonisarch/ES-DE"
DUCKSTATION_COVERS = HOME / ".local/share/duckstation/covers"
PCSX2_COVERS = HOME / ".var/app/net.pcsx2.PCSX2/config/PCSX2/covers"
DOLPHIN_COVERS = HOME / ".var/app/org.DolphinEmu.dolphin-emu/cache/dolphin-emu/GameCovers"
EXTS_CAPA = (".png", ".jpg", ".jpeg", ".webp")


def _capas_dir(cfg: dict, code: str) -> Path | None:
    info = cfg.get("systems", {}).get(code) or cfg.get("heavy_systems", {}).get(code)
    if not info or not info.get("capas"):
        return None
    d = Path(cfg["pc"]["capas_root"]).expanduser() / info["capas"] / "Named_Boxarts"
    return d if d.is_dir() else None


def _roms(cfg: dict, code: str) -> list[Path]:
    info = cfg.get("systems", {}).get(code) or cfg.get("heavy_systems", {}).get(code) or {}
    pasta = Path(cfg["pc"]["roms_root"]).expanduser() / code
    exts = {"." + e.lower().lstrip(".") for e in info.get("exts", [])}
    if not pasta.is_dir():
        return []
    return sorted(f for f in pasta.iterdir() if f.is_file() and f.suffix.lower() in exts)


def _capa_de(capas: Path, stem: str) -> Path | None:
    for ext in EXTS_CAPA:
        p = capas / (stem + ext)
        if p.is_file():
            return p
    return None


def _link(destino: Path, origem: Path, apply: bool) -> dict:
    """Cria destino -> origem. Substitui um link que já existe e aponta para outro
    lugar; recusa qualquer outro arquivo ou pasta real."""
    if destino.is_symlink():
        if destino.resolve() == origem.resolve():
            return {"destino": str(destino), "estado": "ok"}
        if apply:
            destino.unlink()
    elif destino.exists():
        if destino.is_dir() and not any(destino.iterdir()):
            if apply:
                destino.rmdir()
        else:
            return {"destino": str(destino), "estado": "pulado", "motivo": "já existe e não é um link do PyRetro"}
    if apply:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.symlink_to(origem, target_is_directory=origem.is_dir())
    return {"destino": str(destino), "estado": "criado" if apply else "a criar"}


def esde_sistemas(esde_home: Path = ESDE_HOME) -> list[tuple[str, str]]:
    """[(nome do sistema no ES-DE, pasta de ROM)] lidos do es_systems.xml personalizado."""
    xml = esde_home / "custom_systems" / "es_systems.xml"
    if not xml.is_file():
        return []
    out = []
    for s in ET.parse(xml).getroot().iter("system"):
        nome, caminho = s.findtext("name"), s.findtext("path")
        if nome and caminho:
            out.append((nome, Path(caminho).name))
    return out


def plano_esde(cfg: dict, apply: bool, esde_home: Path = ESDE_HOME) -> list[dict]:
    out = []
    for nome, code in esde_sistemas(esde_home):
        capas = _capas_dir(cfg, code)
        if capas is None:
            out.append({"alvo": f"ES-DE {nome}", "destino": "", "estado": "pulado", "motivo": f"sem pasta de capas para {code}"})
            continue
        out.append({"alvo": f"ES-DE {nome}", **_link(esde_home / "downloaded_media" / nome / "covers", capas, apply)})
    return out


def serial_ps2(iso: Path) -> str | None:
    """Serial (ex.: SLUS-21065) lido do SYSTEM.CNF de uma .iso do PS2 (ISO 9660,
    setores de 2048 bytes). Devolve None para outros formatos ou se não achar."""
    if iso.suffix.lower() != ".iso":
        return None
    try:
        with open(iso, "rb") as f:
            f.seek(16 * 2048)
            pvd = f.read(2048)
            if pvd[1:6] != b"CD001":
                return None
            lba = int.from_bytes(pvd[158:162], "little")
            tam = int.from_bytes(pvd[166:170], "little")
            f.seek(lba * 2048)
            raiz = f.read(min(tam, 64 * 2048))
            i = 0
            while i < len(raiz) and raiz[i]:
                n = raiz[i]
                nome = raiz[i + 33:i + 33 + raiz[i + 32]]
                if nome.upper().startswith(b"SYSTEM.CNF"):
                    ext = int.from_bytes(raiz[i + 2:i + 6], "little")
                    f.seek(ext * 2048)
                    cnf = f.read(512).decode("ascii", "ignore")
                    m = re.search(r"BOOT2?\s*=\s*cdrom0:\\?([A-Z]{4})_(\d{3})\.(\d{2})", cnf)
                    return f"{m.group(1)}-{m.group(2)}{m.group(3)}" if m else None
                i += n
                if i < len(raiz) and not raiz[i]:
                    i = (i // 2048 + 1) * 2048
    except OSError:
        return None
    return None


def _guardar_baixada(destino: Path, apply: bool) -> dict | None:
    """O PCSX2 prefere a capa baixada por ele (nome = serial) à nossa. Se já
    existe um arquivo real com esse nome, ele vai para a subpasta
    `_baixadas_pelo_emulador` (nada é apagado) e o nome passa a ser um link."""
    if destino.is_symlink() or not destino.is_file():
        return None
    reserva = destino.parent / "_baixadas_pelo_emulador"
    if apply:
        reserva.mkdir(exist_ok=True)
        destino.rename(reserva / destino.name)
    return {"alvo": "PCSX2", "destino": str(destino), "estado": "guardada" if apply else "a guardar",
            "motivo": f"capa baixada pelo emulador vai para {reserva.name}/"}


def _por_rom(cfg: dict, code: str, pasta: Path, alvo: str, apply: bool, por_serial=None) -> list[dict]:
    capas = _capas_dir(cfg, code)
    out = []
    if capas is None:
        return [{"alvo": alvo, "destino": "", "estado": "pulado", "motivo": f"sem pasta de capas para {code}"}]
    for rom in _roms(cfg, code):
        capa = _capa_de(capas, rom.stem)
        if capa is None:
            out.append({"alvo": alvo, "destino": rom.stem, "estado": "sem capa"})
            continue
        out.append({"alvo": alvo, **_link(pasta / (rom.stem + capa.suffix), capa, apply)})
        serial = por_serial(rom) if por_serial else None
        if serial:
            for ext in EXTS_CAPA:
                aviso = _guardar_baixada(pasta / (serial + ext), apply)
                if aviso:
                    out.append(aviso)
            out.append({"alvo": alvo, **_link(pasta / (serial + capa.suffix), capa, apply)})
    return out


def id_dolphin(rom: Path) -> str | None:
    """ID de 6 caracteres (ex.: GM8E01) lido do cabeçalho. .iso: bytes 0-5;
    .wbfs: cabeçalho do disco começa em 0x200."""
    try:
        with open(rom, "rb") as f:
            ext = rom.suffix.lower()
            if ext == ".iso":
                bruto = f.read(6)
            elif ext == ".wbfs":
                f.seek(0x200)
                bruto = f.read(6)
            else:
                return None
    except OSError:
        return None
    texto = bruto.decode("ascii", "ignore")
    return texto if re.fullmatch(r"[A-Z0-9]{6}", texto) else None


def plano_dolphin(cfg: dict, apply: bool, pasta: Path = DOLPHIN_COVERS) -> list[dict]:
    out = []
    for code in ("NGC", "WII"):
        capas = _capas_dir(cfg, code)
        if capas is None:
            continue
        for rom in _roms(cfg, code):
            capa = _capa_de(capas, rom.stem)
            if capa is None:
                out.append({"alvo": f"Dolphin {code}", "destino": rom.stem, "estado": "sem capa"})
                continue
            if capa.suffix.lower() != ".png":
                out.append({"alvo": f"Dolphin {code}", "destino": rom.stem, "estado": "pulado",
                            "motivo": "o Dolphin só lê capa .png"})
                continue
            gid = id_dolphin(rom)
            if gid is None:
                out.append({"alvo": f"Dolphin {code}", "destino": rom.name, "estado": "pulado",
                            "motivo": "só leio o ID de .iso e .wbfs"})
                continue
            out.append({"alvo": f"Dolphin {code}", **_link(pasta / (gid + ".png"), capa, apply)})
    return out


def plano(cfg: dict, apply: bool) -> list[dict]:
    """Relatório (e, com apply, criação) dos links de capa para todos os destinos."""
    return (plano_esde(cfg, apply)
            + _por_rom(cfg, "PS", DUCKSTATION_COVERS, "DuckStation", apply)
            + _por_rom(cfg, "PS2", PCSX2_COVERS, "PCSX2", apply, serial_ps2)
            + plano_dolphin(cfg, apply))
