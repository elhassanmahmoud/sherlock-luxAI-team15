"""Prüft den neuen 80er-Kartenblock in losen und komprimierten Versuchsartefakten."""
from pathlib import Path
import gzip
import re
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import seedpruefung

def contains(path):
    compressed=path.name.endswith(seedpruefung.GZIP_LABELS)
    with (gzip.open(path,"rb") if compressed else path.open("rb")) as source:
        tail=b""
        while True:
            block=source.read(512*1024)
            if not block:return bool(seedpruefung.IDS.search(tail))
            data=tail+block
            if b"1603860" in data and any(m.end()<len(data)-32 for m in seedpruefung.IDS.finditer(data)):
                return True
            tail=data[-64:]


if __name__=="__main__":
    seedpruefung.contains=contains
    seedpruefung.HERE=HERE
    seedpruefung.OWN="experiments/analysis/v16_finalwoche_20261122/signalstudie/kombi/"
    seedpruefung.IDS=re.compile(rb"(?<![\w.])1603860[0-7][0-9](?![\w.])")
    seedpruefung.main()
