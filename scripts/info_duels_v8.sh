#!/bin/bash
# 22.10.2026: Zusatzinformation fuer die Teamentscheidung zu V8 (KEIN Gate, keine automatische Uebernahme):
# V8 direkt gegen V7 auf 508620-509019 (400 Karten, 800 Spiele) und gegen V3 auf 509020-509219 (400 Spiele).
cd "$(dirname "$0")/.."
LOG=experiments/info_duels_v8.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
echo "[$(date +%H:%M)] Start Info-Duelle V8" >> $LOG
$PY -m scripts.par_eval --weights $E/v8_Bsnpdroc.pth --first 8620 --n 400 --workers ${WORKERS:-12} \
    --opponents self:$E/v7_Bsnpd.pth --out $D/I22_v8_vs_v7_8620.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $E/v8_Bsnpdroc.pth --first 9020 --n 200 --workers ${WORKERS:-12} \
    --opponents self:$E/all18_v3.pth --out $D/I22_v8_vs_v3_9020.csv 2>&1 | grep -v geladen >> $LOG
for f in I22_v8_vs_v7_8620 I22_v8_vs_v3_9020; do
    $PY - <<PY >> $LOG
import sys; sys.path.insert(0, "scripts")
from v5_gates import direct_interval
m, lo, hi, n = direct_interval("$D/$f.csv")
print(f"$f: {m:.4f} [{lo:.4f}; {hi:.4f}] aus {n} Spielen (nur Information)")
PY
done
echo "[$(date +%H:%M)] Ende" >> $LOG
