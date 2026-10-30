#!/bin/bash
# 30.10.2026: Battle-Bestaetigung nach Plan-Nachtrag 30.10., 23:01 (docs/superpowers/plans/2026-10-29-battle-push.md).
# Ein Kandidat experiments/ensembles/battle_NAME.pth gegen V11 auf 800 frischen Karten 810400-811199 gegen die
# 6 Gegner des Dev-A-Screens und default, Direktduell gegen V11 auf 811200-811599 (800 Spiele). Huerden:
# scripts/league_gates.py battle. Der Block gilt fuer genau einen Kandidaten. Die Abgabe aendert dieses Skript
# nicht; Uebernahme nach bestandener Bestaetigung mit scripts/release_candidate.py.
#   bash scripts/battle_confirm.sh NAME        (WORKERS, Default 12)
cd "$(dirname "$0")/.."
NAME=$1
PY=.venv/bin/python
D=experiments/compare/battle
LOG=experiments/pipeline_battle_gate.log
R=experiments/releases
E=experiments/ensembles
V11=$R/20261030_v11_baseline/agent_p0.pth
CAND=$E/battle_$NAME.pth
OPP="solution92,sol92_sq,self:$R/20261022_all18_v3/agent_p0.pth,self:$R/20261022_v7_Bsnpd/agent_p0.pth"
OPP="$OPP,self:$E/league_nets6.pth,self:$E/threat6.pth,default"
[ -n "$NAME" ] && [ -f $CAND ] || { echo "fehlt: $CAND"; exit 1; }
other=$(ls $D/GB_*_conf.csv 2>/dev/null | grep -v "/GB_V11_conf.csv" | grep -v "/GB_${NAME}_conf.csv")
[ -n "$other" ] && { echo "Der Block hat schon eine Battle-Bestaetigung: $other"; exit 1; }
run() {  # run GEWICHTE FIRST N GEGNER AUSGABE
    [ -f "$5" ] && return 0
    $PY -m scripts.par_eval --weights "$1" --first $2 --n $3 --workers ${WORKERS:-12} --opponents "$4" --out "$5" \
        2>&1 | grep -v geladen | tail -1 >> $LOG
}
echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung: Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))," \
    "Referenz V11, Code $(git rev-parse --short HEAD)" >> $LOG
run $V11 310400 800 "$OPP" $D/GB_V11_conf.csv
run $CAND 310400 800 "$OPP" $D/GB_${NAME}_conf.csv
run $CAND 311200 400 "self:$V11" $D/GB_${NAME}_confdir.csv
$PY -m scripts.league_gates battle $D/GB_V11_conf.csv $D/GB_${NAME}_conf.csv $D/GB_${NAME}_confdir.csv \
    --direct-opponent "self:$V11" >> $LOG 2>&1
echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung $NAME fertig" >> $LOG
tail -14 $LOG
