#!/bin/bash
# Groessere Entwicklungsmessung: dev_hard330 + dev_easy330 (nur Solution_92), V3-Werte aus der Kartensuche.
#   bash experiments/analysis/hard_map_training_20261021/dev_eval2.sh NAME WORKERS [WEIGHTS] -- [--set k=v ...]
cd "$(dirname "$0")/../../.."
name=$1; workers=$2; shift 2
weights=agents/sherlock/weights/agent_p0.pth
if [ "$1" != "--" ] && [ -n "$1" ]; then weights=$1; shift; fi
[ "$1" = "--" ] && shift
H=experiments/analysis/hard_map_training_20261021
D=experiments/compare/regeln
for set in hard330 easy330; do
    [ -f $D/D22_${name}_${set}.csv ] || .venv/bin/python -m scripts.par_eval --weights $weights "$@" --opponents solution92 \
        --seed-list $H/dev_${set}.json --workers $workers --out $D/D22_${name}_${set}.csv 2>&1 | grep -v geladen
done
