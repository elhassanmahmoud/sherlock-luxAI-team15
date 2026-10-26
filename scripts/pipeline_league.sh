#!/bin/bash
# 26.10.2026: Gegner-Liga nach docs/superpowers/plans/2026-10-26-league.md.
#   bash scripts/pipeline_league.sh
# 1) 6 Netze full_rules_v10 (Starts 73-78, je 4000 Spiele, Gegnerplan league, Pool V10 + V7);
#    parallel dazu (niedrige Prioritaet) V10-Referenz auf Auswahl- und Bestaetigungsblock.
# 2) Kandidaten L24 (V10 + 6 neue) und L6 (6 neue) auf dem Auswahlblock 700000-700199, mit Direktduell.
# 3) Nur bei bestandener Auswahl: einmalige Bestaetigung (701000-701799, direkt 702000-702399).
#    Abgabe-Gewichte bleiben unberuehrt; eine Uebernahme erfolgt getrennt nach dem Plan.
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_league.log
PY=.venv/bin/python
E=experiments/ensembles
D=experiments/compare/league
W=${WORKERS:-12}
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
V7=experiments/releases/20261022_v7_Bsnpd/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
OPPS="solution92,sol92_sq,sol92_weak,self:$OLD3,default"
R=experiments/runs/20261026_full_rules_v10_s
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
need() { for f in "$@"; do [ -f "$f" ] || { log "FEHLER: $f fehlt -> Abbruch"; exit 1; }; done; }
mkdir -p $D
log "Start (Commit $(git rev-parse --short HEAD), V10 $(shasum -a 256 $V10 | cut -c1-16))"

$PY -m scripts.run_experiments --variants full_rules_v10 --starts 6 --first-start 73 --games 4000 \
    --val-every 500 --workers 6 --date 20261026 --tag league --extra --no-test \
    --opponent-plan league --pool $V10 $V7 > experiments/batch_20261026_league.log 2>&1 &
TRAIN=$!
[ -f $D/V10_ref_S.csv ] || nice -n 10 $PY -m scripts.par_eval --weights $V10 --first 200000 --n 200 \
    --workers 8 --opponents $OPPS --out $D/V10_ref_S.csv 2>&1 | grep -v geladen >> $LOG
[ -f $D/V10_ref_C.csv ] || nice -n 10 $PY -m scripts.par_eval --weights $V10 --first 201000 --n 800 \
    --workers 8 --opponents $OPPS --out $D/V10_ref_C.csv 2>&1 | grep -v geladen >> $LOG
need $D/V10_ref_S.csv $D/V10_ref_C.csv
log "V10-Referenz fertig, warte auf Training"
wait $TRAIN
log "Training: $(tail -1 experiments/batch_20261026_league.log)"
NETS=""
for s in 73 74 75 76 77 78; do
    need ${R}${s}_league/weights/agent.pth
    NETS="$NETS ${R}${s}_league/weights/agent.pth"
done
[ -f $E/league_mix24.pth ] || $PY -m scripts.build_ensemble --out $E/league_mix24.pth $V10 $NETS >> $LOG 2>&1
[ -f $E/league_nets6.pth ] || $PY -m scripts.build_ensemble --out $E/league_nets6.pth $NETS >> $LOG 2>&1
shasum -a 256 $E/league_mix24.pth $E/league_nets6.pth >> $LOG
for c in mix24 nets6; do
    [ -f $D/L_${c}_S.csv ] || $PY -m scripts.par_eval --weights $E/league_$c.pth --first 200000 --n 200 \
        --workers $W --opponents $OPPS --out $D/L_${c}_S.csv 2>&1 | grep -v geladen >> $LOG
    [ -f $D/L_${c}_S_direct.csv ] || $PY -m scripts.par_eval --weights $E/league_$c.pth --first 200000 \
        --n 200 --workers $W --opponents self:$V10 --out $D/L_${c}_S_direct.csv 2>&1 | grep -v geladen >> $LOG
    need $D/L_${c}_S.csv $D/L_${c}_S_direct.csv
done
OUT=$($PY -m scripts.league_gates select $D/V10_ref_S.csv L24 $D/L_mix24_S.csv $D/L_mix24_S_direct.csv \
      L6 $D/L_nets6_S.csv $D/L_nets6_S_direct.csv 2>&1)
echo "$OUT" >> $LOG
PICK=$(echo "$OUT" | sed -n 's/^AUSWAHL: //p')
case $PICK in
    L24) CAND=$E/league_mix24.pth ;;
    L6) CAND=$E/league_nets6.pth ;;
    keine) log "Kein Kandidat -> Ende; Bestaetigungs- und Direktblock fuer Kandidaten unberuehrt, V10 bleibt"; exit 0 ;;
    *) log "FEHLER: Auswahl nicht auswertbar -> Abbruch"; exit 1 ;;
esac
log "Auswahl $PICK ($CAND) -> einmalige frische Bestaetigung"
$PY -m scripts.par_eval --weights $CAND --first 201000 --n 800 --workers $W --opponents $OPPS \
    --out $D/${PICK}_C.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $CAND --first 202000 --n 400 --workers $W --opponents self:$V10 \
    --out $D/${PICK}_D_direct.csv 2>&1 | grep -v geladen >> $LOG
need $D/${PICK}_C.csv $D/${PICK}_D_direct.csv
$PY -m scripts.league_gates confirm $D/V10_ref_C.csv $D/${PICK}_C.csv $D/${PICK}_D_direct.csv >> $LOG 2>&1
log "Ende"
