#!/bin/bash
# 22.10.2026: V8-Ablauf nach docs/superpowers/plans/2026-10-22-v8.md.
#   bash scripts/pipeline_v8.sh KANDIDAT.pth NAME
# 1) Zufallsblock 506 020-506 219 (Kandidat und Referenz REF):
#    weiter nur bei Solution_92 >= MIN_SEL_DELTA und default >= 99 % (Plan V8: +1 pp gegen V7).
# 2) Einmalige frische Bestaetigung: 506 220-507 019 (800 Karten, Kandidat und REF) und
#    507 020-507 219 direkt gegen REF. Gates: scripts/v5_gates.py. Abgabe-Gewichte unberuehrt.
cd "$(dirname "$0")/.."
CAND=$1; NAME=$2
LOG=experiments/pipeline_v8.log
PY=.venv/bin/python
D=experiments/compare/regeln
W=${WORKERS:-12}
REF=${REF:-experiments/ensembles/all18_v3.pth}  # Referenz = aktuelle Abgabe (V3 oder nach Uebernahme V7)
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16)) gegen REF $REF ($(shasum -a 256 $REF | cut -c1-16))"
[ -f $D/V8_ref_6020.csv ] || $PY -m scripts.par_eval --weights $REF --first 6020 --n 200 \
    --workers $W --out $D/V8_ref_6020.csv 2>&1 | grep -v geladen >> $LOG
[ -f $D/V8_${NAME}_6020.csv ] || $PY -m scripts.par_eval --weights $CAND --first 6020 --n 200 --workers $W \
    --out $D/V8_${NAME}_6020.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V8_ref_6020.csv $D/V8_${NAME}_6020.csv 2>&1 | grep -E "default |solution92" >> $LOG
if ! $PY scripts/v5_gates.py selection $D/V8_ref_6020.csv $D/V8_${NAME}_6020.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
[ -f $D/V8_ref_6220.csv ] || $PY -m scripts.par_eval --weights $REF --first 6220 --n 800 \
    --workers $W --out $D/V8_ref_6220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 6220 --n 800 --workers $W \
    --out $D/V8_${NAME}_6220.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 7020 --n 200 --workers $W \
    --opponents self:$REF --out $D/V8_${NAME}_direct_7020.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V8_ref_6220.csv $D/V8_${NAME}_6220.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/V8_ref_6220.csv $D/V8_${NAME}_6220.csv $D/V8_${NAME}_direct_7020.csv >> $LOG
log "Ende $NAME"
