#!/bin/bash
# 22.10.2026: V7-Ablauf nach docs/superpowers/plans/2026-10-22-v7.md.
#   bash scripts/pipeline_v7.sh KANDIDAT.pth NAME
# 1) Zufallsblock 505 220-505 419 (Kandidat und V3):
#    weiter nur bei Solution_92 >= +3 pp und default >= 99 %.
# 2) Einmalige frische Bestaetigung: 505 420-505 819 (400 Karten, Kandidat und V3) und
#    505 820-506 019 direkt gegen V3. Gates: scripts/v5_gates.py. Abgabe-Gewichte unberuehrt.
cd "$(dirname "$0")/.."
CAND=$1; NAME=$2
LOG=experiments/pipeline_v7.log
PY=.venv/bin/python
D=experiments/compare/regeln
W=${WORKERS:-12}
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))"
[ -f $D/V7_v3_5220.csv ] || $PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 5220 --n 200 \
    --workers $W --out $D/V7_v3_5220.csv 2>&1 | grep -v geladen >> $LOG
[ -f $D/V7_${NAME}_5220.csv ] || $PY -m scripts.par_eval --weights $CAND --first 5220 --n 200 --workers $W \
    --out $D/V7_${NAME}_5220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V7_v3_5220.csv $D/V7_${NAME}_5220.csv 2>&1 | grep -E "default |solution92" >> $LOG
if ! $PY scripts/v5_gates.py selection $D/V7_v3_5220.csv $D/V7_${NAME}_5220.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
[ -f $D/V7_v3_5420.csv ] || $PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 5420 --n 400 \
    --workers $W --out $D/V7_v3_5420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 5420 --n 400 --workers $W \
    --out $D/V7_${NAME}_5420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 5820 --n 200 --workers $W \
    --opponents self:experiments/ensembles/all18_v3.pth --out $D/V7_${NAME}_direct_5820.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V7_v3_5420.csv $D/V7_${NAME}_5420.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/V7_v3_5420.csv $D/V7_${NAME}_5420.csv $D/V7_${NAME}_direct_5820.csv >> $LOG
log "Ende $NAME"
