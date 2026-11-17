#!/bin/bash
# Prüfung des empfohlenen Pakets unter Python 3.10 (17.11.2026, abends, nach Mahmouds Ja zur Homebrew-Installation).
# Wie im Codex-Auftrag (docs/AUFTRAG_CODEX_20261117.md, Aufgabe 2): ein Spiel Sherlock gegen Sherlock in der
# Projektumgebung aufzeichnen und unter Python 3.10 nachspielen (erwartet: 0 abweichende Aktionen), danach 8 ganze
# Spiele im unveränderten Kursrunner unter Python 3.10. Alles aus einer eingefrorenen Kopie des Quellstands.
#   run_py310.sh SCRATCH_DIR
set -u
S=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
D=$MAIN/experiments/analysis/deve_20261117
ZIP=experiments/candidates/devf_20261117/agent_p9_s10_halter.zip
PY=$MAIN/.venv/bin/python
PY310=$S/venv310/bin/python
HEAD=$(git -C $MAIN rev-parse --short HEAD)
FROZEN=$S/frozen_py310_$HEAD
log() { echo "$(date '+%H:%M:%S') $*"; }

[ -d $FROZEN ] || { mkdir -p $FROZEN && git -C $MAIN archive HEAD | tar -x -C $FROZEN; }
log "START Quelle $HEAD"
$PY --version; $PY310 --version
$PY310 -c "import torch, numpy, scipy; print('3.10: torch', torch.__version__, 'numpy', numpy.__version__, 'scipy', scipy.__version__)"
shasum -a 256 $FROZEN/$ZIP

# 1) Paketcode gleich dem eingefrorenen agents/sherlock?
rm -rf $S/py310_pkg && mkdir -p $S/py310_pkg && unzip -q $FROZEN/$ZIP -d $S/py310_pkg
same=1
for f in $S/py310_pkg/sherlock/*.py; do cmp -s $f $FROZEN/agents/sherlock/$(basename $f) || { echo "ABWEICHUNG $(basename $f)"; same=0; }; done
log "Paketcode gleich agents/sherlock: $same"

# 2) Aufzeichnen (Projektumgebung) und unter 3.10 nachspielen
cd $FROZEN || exit 1
rm -f $S/py310_spiel.pkl
$PY scripts/xversion_replay.py record $ZIP $S/py310_spiel.pkl --seed 4242 2>&1 | grep -v Warn
log "aufgezeichnet"
cd $S || exit 1
$PY310 -I $FROZEN/scripts/xversion_replay.py replay $FROZEN/$ZIP $S/py310_spiel.pkl 2>&1 | grep -v Warn
log "nachgespielt"

# 3) 8 ganze Kursrunner-Spiele unter 3.10 (Kursregel 3 Matches in der 3.10-Umgebung setzen)
cd $FROZEN || exit 1
$PY310 -m scripts.set_match_count
OUT=$D/kursrunner_p9_s10_halter_py310.json
[ -f $OUT ] || $PY310 -m scripts.check_candidate_runner --weights $S/py310_pkg/sherlock/weights/agent.pth --out $OUT 2>&1 | grep -v Warn
log "PY310_DONE"
