#!/bin/bash
# 22.10.2026: V5-Ablauf nach docs/superpowers/plans/2026-10-22-v5-combination.md.
#   bash scripts/pipeline_v5.sh KANDIDAT.pth NAME
# 1) Zufallsblock 503 820-504 019 (Referenz V3: experiments/compare/regeln/P21_v3_3820.csv):
#    weiter nur bei Solution_92 >= +3 pp und default >= 99 %.
# 2) Einmalige frische Bestaetigung: 503 420-503 619 (Kandidat und V3, beide Gegner) und
#    503 620-503 819 direkt gegen V3. Gates: scripts/v5_gates.py. Abgabe-Gewichte unberuehrt.
cd "$(dirname "$0")/.."
CAND=$1; NAME=$2
LOG=experiments/pipeline_v5.log
PY=.venv/bin/python
D=experiments/compare/regeln
W=${WORKERS:-12}
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))"
[ -f $D/V5_${NAME}_3820.csv ] || $PY -m scripts.par_eval --weights $CAND --first 3820 --n 200 --workers $W \
    --out $D/V5_${NAME}_3820.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/P21_v3_3820.csv $D/V5_${NAME}_3820.csv 2>&1 | grep -E "default |solution92" >> $LOG
if ! $PY scripts/v5_gates.py selection $D/P21_v3_3820.csv $D/V5_${NAME}_3820.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
[ -f $D/V5_v3_3420.csv ] || $PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 3420 --n 200 \
    --workers $W --out $D/V5_v3_3420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 3420 --n 200 --workers $W \
    --out $D/V5_${NAME}_3420.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 3620 --n 200 --workers $W \
    --opponents self:experiments/ensembles/all18_v3.pth --out $D/V5_${NAME}_direct_3620.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/V5_v3_3420.csv $D/V5_${NAME}_3420.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/V5_v3_3420.csv $D/V5_${NAME}_3420.csv $D/V5_${NAME}_direct_3620.csv >> $LOG
log "Ende $NAME"
