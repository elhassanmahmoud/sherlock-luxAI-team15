#!/bin/bash
# 22.10.2026: V10-Ablauf nach docs/superpowers/plans/2026-10-22-v10.md.
#   bash scripts/pipeline_v10.sh KANDIDAT.pth NAME
# 1) Zufallsblock 507 220-507 419 (Kandidat und Referenz REF):
#    weiter nur bei Solution_92 >= MIN_SEL_DELTA und default >= 99 % (Plan V10: +1 pp gegen V7).
# 2) Einmalige frische Bestaetigung: 507 420-508 219 (800 Karten, Kandidat und REF) und
#    508 220-508 619 (400 Karten) direkt gegen REF. Gates: scripts/v5_gates.py. Abgabe-Gewichte unberuehrt.
cd "$(dirname "$0")/.."
CAND=$1; NAME=$2
LOG=experiments/pipeline_v10.log
PY=.venv/bin/python
D=experiments/compare/regeln
W=${WORKERS:-12}
REF=${REF:-experiments/ensembles/all18_v3.pth}  # Referenz = aktuelle Abgabe (V3 oder nach Uebernahme V7)
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16)) gegen REF $REF ($(shasum -a 256 $REF | cut -c1-16))"
[ -f $D/V10_ref_7220.csv ] || $PY -m scripts.par_eval --weights $REF --first 7220 --n 200 \
    --workers $W --out $D/V10_ref_7220.csv 2>&1 | grep -v geladen >> $LOG
[ -f $D/V10_${NAME}_7220.csv ] || $PY -m scripts.par_eval --weights $CAND --first 7220 --n 200 --workers $W \
    --out $D/V10_${NAME}_7220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V10_ref_7220.csv $D/V10_${NAME}_7220.csv 2>&1 | grep -E "default |solution92" >> $LOG
if ! $PY scripts/v5_gates.py selection $D/V10_ref_7220.csv $D/V10_${NAME}_7220.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
[ -f $D/V10_ref_7420.csv ] || $PY -m scripts.par_eval --weights $REF --first 7420 --n 800 \
    --workers $W --out $D/V10_ref_7420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 7420 --n 800 --workers $W \
    --out $D/V10_${NAME}_7420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 8220 --n 400 --workers $W \
    --opponents self:$REF --out $D/V10_${NAME}_direct_8220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V10_ref_7420.csv $D/V10_${NAME}_7420.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/V10_ref_7420.csv $D/V10_${NAME}_7420.csv $D/V10_${NAME}_direct_8220.csv >> $LOG
log "Ende $NAME"
