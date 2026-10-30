#!/bin/bash
# V11-Niederlagen auf Dev A mit Ground Truth nachmessen (nur lesen, Gewichte = feste V11-Kopie).
cd /Users/elhassanmahmoud/Documents/AKI_LuxAgent15
PY=.venv/bin/python
W=experiments/releases/20261030_v11_baseline/agent_p0.pth
D=experiments/compare/battle
O=experiments/analysis/battle
L6="self:experiments/ensembles/league_nets6.pth"
run() { [ -f "$O/$4" ] || $PY -m scripts.par_losses --weights $W --games $1 --opponent "$2" --which $3 ${5:+--limit $5} --workers 14 --out $O/$4 2>&1 | tail -1; }
run $D/D_mix36c_as.csv sol92_sq lost L_V11_sol92_sq_lost.csv
run $D/D_mix36c_as.csv sol92_sq won L_V11_sol92_sq_won.csv 160
run $D/D_mix36c_as.csv solution92 lost L_V11_solution92_lost.csv
run $D/D_mix36c_as_hold.csv "$L6" lost L_V11_league6_lost.csv
run $D/D_mix36c_as_hold.csv "$L6" won L_V11_league6_won.csv 160
echo FERTIG $(date '+%H:%M')
# Energiebilanz (Sap, Void, Kollision, Tod) der V11-Spiele gegen sol92_sq auf Dev A: verloren und 160 gewonnene.
cd /Users/elhassanmahmoud/Documents/AKI_LuxAgent15
PY=.venv/bin/python
W=experiments/releases/20261030_v11_baseline/agent_p0.pth
D=experiments/compare/battle
O=experiments/analysis/battle
[ -f $O/M_V11_sol92_sq_lost.json ] || $PY scripts/mechanism_probe.py --weights $W --opponent sol92_sq --games $D/D_mix36c_as.csv --which lost --workers 14 --out $O/M_V11_sol92_sq_lost.json 2>&1 | tail -2
[ -f $O/M_V11_sol92_sq_won.json ] || $PY scripts/mechanism_probe.py --weights $W --opponent sol92_sq --games $D/D_mix36c_as.csv --which won --limit 160 --workers 14 --out $O/M_V11_sol92_sq_won.json 2>&1 | tail -2
echo FERTIG2 $(date '+%H:%M')
