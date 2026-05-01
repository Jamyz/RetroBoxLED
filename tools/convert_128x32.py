from pathlib import Path
from PIL import Image

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
TARGET_W = 128
TARGET_H = 32
# ─────────────────────────────────────────────

def convert_image(src: Path, dst: Path):
    """
    Redimensionne l'image en respectant l'aspect ratio,
    puis la centre sur un fond noir 128x32.
    Aucun rognage, aucune déformation.
    """
    with Image.open(src) as img:
        img = img.convert("RGBA")
        orig_w, orig_h = img.size

        ratio = min(TARGET_W / orig_w, TARGET_H / orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)

        resized = img.resize((new_w, new_h), Image.LANCZOS)

        canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 255))

        offset_x = (TARGET_W - new_w) // 2
        offset_y = (TARGET_H - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y), resized)

        canvas.convert("RGB").save(dst, "PNG", optimize=True)


def ask_input_dir() -> Path:
    """Demande interactivement où se trouvent les PNG à convertir."""
    print("\n📍 OÙ SE TROUVENT VOS PNG ?")
    print("─" * 40)
    print("  1  →  Lecteur local  (ex: D:\\gamelist_images)")
    print("  2  →  Réseau / NAS   (ex: \\\\192.168.1.1\\share\\gamelist_images)")
    print("─" * 40)

    while True:
        choix = input("Votre choix (1 ou 2) : ").strip()

        if choix in ("1", "2"):
            label = "Chemin du dossier  : " if choix == "1" else "Chemin réseau      : "
            chemin = input(label).strip().strip('"')
            p = Path(chemin)
            if p.exists() and p.is_dir():
                return p
            print(f"❌ Dossier introuvable : {chemin}\n   Vérifie le chemin et réessaie.\n")
        else:
            print("⚠️  Tape 1 ou 2.\n")


def main():
    print("🖼️  CONVERSION PNG → 128x32 px")
    print("=" * 60)

    input_root = ask_input_dir()
    print(f"\n✅ Dossier source : {input_root}\n")

    # Dossier de sortie : _128x32 à côté du dossier source
    output_root = input_root.parent / (input_root.name + "_128x32")

    # Collecte tous les PNG récursivement
    png_files = [p for p in input_root.rglob("*.png")]

    total   = len(png_files)
    done    = 0
    skipped = 0
    errors  = 0

    print(f"🔢 {total} images trouvées")
    print(f"📂 Sortie : {output_root}")
    print("=" * 60)

    for i, src in enumerate(png_files, 1):
        # Reproduction de l'arborescence dans le dossier de sortie
        relative = src.relative_to(input_root)

        # Nom basé sur le stem du fichier (qui correspond déjà au stem de <path>)
        dst_dir = output_root / relative.parent
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name

        if dst.exists():
            skipped += 1
            print(f"  {i:5d}/{total} ⏭️  {relative} (déjà converti)")
            continue

        try:
            convert_image(src, dst)
            done += 1
            print(f"  {i:5d}/{total} ✅ {relative}")
        except Exception as e:
            errors += 1
            print(f"  {i:5d}/{total} ❌ {relative} — {e}")

    print("=" * 60)
    print("🎉 TERMINÉ !")
    print(f"✅ {done} images converties")
    print(f"⏭️  {skipped} déjà présentes (ignorées)")
    print(f"❌ {errors} erreurs")
    print(f"📂 Résultat : {output_root}")
    input("\nAppuie sur Entrée pour fermer...")


if __name__ == "__main__":
    main()
