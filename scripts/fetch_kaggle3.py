"""Kaggle-Platz-3-Agent (lux3-bot 0.4.8_fn) als TESTGEGNER herunterladen (15.11.2026).

Quelle: https://github.com/andreyd41/lux3-bot/releases/tag/0.4.8 (Apache-2.0), Imitation Learning
mit zwei U-Nets, Kaggle Lux AI Season 3 Platz 3. Das Archiv wird per SHA-256 geprueft und nach
experiments/opponents/kaggle3_lux3_048fn/ entpackt (gitignored, nie Teil der Abgabe).

    python -m scripts.fetch_kaggle3
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://github.com/andreyd41/lux3-bot/releases/download/0.4.8/lux3_0.4.8_fn.tar.gz"
ARCHIVE_SHA256 = "08911888b550aa102a8edae8345be78ce3bac08ce5402fac416d59a2e5503b44"
WEIGHT_SHA256 = {
    "imitation_learning/weights/unit_unet.pth": "f807fdaa29a6410c17012ac7aac10169c4ded3bb7827483ca7c8d0df6bc3d987",
    "imitation_learning/weights/sap_unet.pth": "40053d180d014f5e6ab1692e44680517c358e071255ff703ff3d9699667b4a88",
}
TARGET = ROOT / "experiments" / "opponents" / "kaggle3_lux3_048fn"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(target: Path = TARGET) -> bool:
    """True, wenn der entpackte Agent vollstaendig ist und die Gewichte den erwarteten Hash haben."""
    if not (target / "agent" / "agent.py").is_file():
        return False
    return all((target / rel).is_file() and sha256(target / rel) == digest for rel, digest in WEIGHT_SHA256.items())


def _safe_members(tar: tarfile.TarFile):
    for m in tar.getmembers():
        p = Path(m.name)
        if p.is_absolute() or ".." in p.parts or not (m.isfile() or m.isdir()):
            raise SystemExit(f"Unerwarteter Archiveintrag: {m.name}")
        yield m


def main() -> None:
    if verify():
        print(f"Bereits vorhanden und geprueft: {TARGET}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "lux3.tar.gz"
        print(f"Lade {URL} ...")
        urllib.request.urlretrieve(URL, archive)
        digest = sha256(archive)
        if digest != ARCHIVE_SHA256:
            raise SystemExit(f"SHA-256 stimmt nicht: {digest}")
        if TARGET.exists():
            shutil.rmtree(TARGET)
        TARGET.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            tar.extractall(TARGET, members=list(_safe_members(tar)))
    if not verify():
        raise SystemExit("Entpackter Agent unvollstaendig oder Gewichte veraendert")
    print(f"Fertig und geprueft: {TARGET}")


if __name__ == "__main__":
    sys.exit(main())
