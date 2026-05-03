import os
import re
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import time

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
# OUTPUT_DIR est le dossier "gamelist_images" à côté du script
OUTPUT_DIR = Path(__file__).parent / "gamelist_images"
# ─────────────────────────────────────────────

_INVALID_XML_CHARS = re.compile(
    r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'
    r'|&#(?:x[0-9a-fA-F]+|\d+);'
)

def _is_valid_codepoint(m: re.Match) -> bool:
    s = m.group()
    if not s.startswith("&#"):
        return False
    inner = s[2:-1]
    code = int(inner[1:], 16) if inner.startswith("x") else int(inner)
    return (code == 0x9 or code == 0xA or code == 0xD
            or 0x20 <= code <= 0xD7FF
            or 0xE000 <= code <= 0xFFFD
            or 0x10000 <= code <= 0x10FFFF)

def sanitize_xml(raw: bytes) -> bytes:
    text = raw.decode("utf-8", errors="replace")
    cleaned = _INVALID_XML_CHARS.sub(lambda m: "" if not _is_valid_codepoint(m) else m.group(), text)
    return cleaned.encode("utf-8")

def resolve_image_path(sys_dir: Path, raw_path: str) -> Path:
    p = raw_path.strip()
    if p.startswith("/"):
        return Path(p)
    return sys_dir / p

def sanitize_filename(name: str) -> str:
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    name = name.replace(" ", "")   # Recalbox supprime les espaces dans ses chemins internes
    return name.strip()

def parse_gamelist(gamelist_path: Path):
    raw = gamelist_path.read_bytes()
    cleaned = sanitize_xml(raw)
    root = ET.fromstring(cleaned)
    return root.findall(".//game")


def ask_roms_root() -> Path:
    """Demande interactivement où se trouvent les ROMs."""
    print("\n📍 OÙ SE TROUVENT VOS ROMS ?")
    print("─" * 40)
    print("  1  →  Lecteur local  (ex: D:\\Recalbox\\roms)")
    print("  2  →  Réseau / NAS   (ex: \\\\192.168.1.1\\Recalbox\\roms)")
    print("─" * 40)

    while True:
        choix = input("Votre choix (1 ou 2) : ").strip()

        if choix == "1":
            print("\n💡 Exemple : D:\\Recalbox\\roms  ou  E:\\roms")
            chemin = input("Chemin du dossier roms : ").strip().strip('"')
            p = Path(chemin)
            if p.exists() and p.is_dir():
                return p
            print(f"❌ Dossier introuvable : {chemin}\n   Vérifie la lettre du lecteur et le chemin.\n")

        elif choix == "2":
            print("\n💡 Exemple : \\\\192.168.10.111\\Recalbox\\roms")
            chemin = input("Chemin réseau       : ").strip().strip('"')
            p = Path(chemin)
            if p.exists() and p.is_dir():
                return p
            print(f"❌ Réseau inaccessible : {chemin}")
            print("   Vérifie que le NAS est allumé et le partage correct.\n")

        else:
            print("⚠️  Tape 1 ou 2.\n")


def process_system(sys_dir: Path, sys_index: int, total_systems: int, log_file) -> tuple[int, int, int, int]:
    sys_name   = sys_dir.name
    sys_output = OUTPUT_DIR / sys_name
    os.makedirs(sys_output, exist_ok=True)

    print(f"\n[{sys_index}/{total_systems}] 📁 {sys_name}")

    try:
        games = parse_gamelist(sys_dir / "gamelist.xml")
    except ET.ParseError as e:
        msg = f"[{sys_name}] ERREUR XML : {e}"
        print(f"   ❌ {msg}")
        log_file.write(msg + "\n")
        return 0, 0, 0, 0

    total   = len(games)
    copied  = 0
    skipped = 0
    missing = 0
    print(f"   🎮 {total} jeux trouvés")

    for i, game in enumerate(games, 1):
        path_elem  = game.find("path")
        image_elem = game.find("image")

        if path_elem is None or image_elem is None:
            missing += 1
            continue

        raw_path  = unquote(path_elem.text or "").strip()
        image_raw = unquote(image_elem.text or "").strip()

        if not image_raw or not raw_path:
            missing += 1
            continue

        # Nom issu de <path> : "Asteroids (USA).zip" → "Asteroids(USA)"
        game_name  = sanitize_filename(Path(raw_path).stem)
        src_image  = resolve_image_path(sys_dir, image_raw)
        ext        = src_image.suffix or ".png"
        dst_image  = sys_output / f"{game_name}{ext}"

        if dst_image.exists():
            skipped += 1
            print(f"   {i:4d}/{total} ⏭️  {game_name}{ext} (déjà présente)")
            continue

        if not src_image.exists():
            missing += 1
            print(f"   {i:4d}/{total} ⚠️  MANQUANT : {src_image}")
            log_file.write(f"[{sys_name}] {game_name} → {src_image}\n")
            continue

        shutil.copy2(src_image, dst_image)
        copied += 1
        print(f"   {i:4d}/{total} ✅ {game_name}{ext}")
        time.sleep(0.005)

    print(f"   → ✅ {copied} copiées | ⏭️  {skipped} déjà présentes | ⚠️  {missing} manquantes")
    return total, copied, skipped, missing


def main():
    print("🚀 EXTRACTION GAMELIST — Recalbox → Images renommées")
    print(f"💾 Sortie  : {OUTPUT_DIR}")
    print("=" * 70)

    # ── Demande du chemin ROMs ────────────────────────────────────────────
    roms_root = ask_roms_root()
    print(f"\n✅ Dossier ROMs : {roms_root}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    systems = [d for d in roms_root.iterdir() if d.is_dir() and (d / "gamelist.xml").exists()]
    total_systems = len(systems)
    print(f"📂 {total_systems} systèmes avec gamelist.xml détectés")

    log_path      = OUTPUT_DIR / "images_manquantes.txt"
    grand_games   = 0
    grand_copied  = 0
    grand_skipped = 0
    grand_missing = 0
    systems_done  = 0

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("=== IMAGES MANQUANTES SUR LE NAS ===\n")
        log_file.write(f"Source : {roms_root}\n\n")

        for idx, sys_dir in enumerate(systems, 1):
            games, copied, skipped, missing = process_system(sys_dir, idx, total_systems, log_file)
            grand_games   += games
            grand_copied  += copied
            grand_skipped += skipped
            grand_missing += missing
            if games > 0:
                systems_done += 1

        log_file.write("\n=== RÉSUMÉ ===\n")
        log_file.write(f"Source             : {roms_root}\n")
        log_file.write(f"Systèmes traités   : {systems_done}/{total_systems}\n")
        log_file.write(f"Jeux parcourus     : {grand_games}\n")
        log_file.write(f"Images copiées     : {grand_copied}\n")
        log_file.write(f"Déjà présentes     : {grand_skipped}\n")
        log_file.write(f"Images manquantes  : {grand_missing}\n")

    print("\n" + "=" * 70)
    print("🎉 TERMINÉ !")
    print(f"📁 {systems_done}/{total_systems} systèmes traités")
    print(f"🎮 {grand_games} jeux parcourus")
    print(f"✅ {grand_copied} images copiées")
    print(f"⏭️  {grand_skipped} déjà présentes (ignorées)")
    print(f"⚠️  {grand_missing} images manquantes")
    print(f"📋 Log des erreurs : {log_path}")
    print(f"📂 Dossier sortie  : {OUTPUT_DIR}")
    input("\nAppuie sur Entrée pour fermer...")


if __name__ == "__main__":
    main()