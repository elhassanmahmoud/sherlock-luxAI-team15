#!/bin/bash
# 22.10.2026: V6-Ablauf nach docs/superpowers/plans/2026-10-22-v6.md.
#   bash scripts/pipeline_v6.sh KANDIDAT.pth NAME
# 1) Zufallsblock 504 020-504 219 (Kandidat und V3):
#    weiter nur bei Solution_92 >= +3 pp und default >= 99 %.
# 2) Einmalige frische Bestaetigung: 504 220-504 619 (400 Karten, Kandidat und V3) und
#    504 620-504 819 direkt gegen V3. Gates: scripts/v5_gates.py. Abgabe-Gewichte unberuehrt.
cd "$(dirname "$0")/.."
CAND=$1; NAME=$2
LOG=experiments/pipeline_v6.log
PY=.venv/bin/python
D=experiments/compare/regeln
W=${WORKERS:-12}
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))"
[ -f $D/V6_v3_4020.csv ] || $PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 4020 --n 200 \
    --workers $W --out $D/V6_v3_4020.csv 2>&1 | grep -v geladen >> $LOG
[ -f $D/V6_${NAME}_4020.csv ] || $PY -m scripts.par_eval --weights $CAND --first 4020 --n 200 --workers $W \
    --out $D/V6_${NAME}_4020.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V6_v3_4020.csv $D/V6_${NAME}_4020.csv 2>&1 | grep -E "default |solution92" >> $LOG
if ! $PY scripts/v5_gates.py selection $D/V6_v3_4020.csv $D/V6_${NAME}_4020.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
[ -f $D/V6_v3_4220.csv ] || $PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 4220 --n 400 \
    --workers $W --out $D/V6_v3_4220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 4220 --n 400 --workers $W \
    --out $D/V6_${NAME}_4220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 4620 --n 200 --workers $W \
    --opponents self:experiments/ensembles/all18_v3.pth --out $D/V6_${NAME}_direct_4620.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V6_v3_4220.csv $D/V6_${NAME}_4220.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/V6_v3_4220.csv $D/V6_${NAME}_4220.csv $D/V6_${NAME}_direct_4620.csv >> $LOG
log "Ende $NAME"
