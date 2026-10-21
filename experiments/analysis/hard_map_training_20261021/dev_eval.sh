#!/bin/bash
# Schnelle Entwicklungsmessung einer Variante auf dev_hard150 + dev_easy60 (nur Solution_92).
#   bash experiments/analysis/hard_map_training_20261021/dev_eval.sh NAME WORKERS [--set k=v ...]
cd "$(dirname "$0")/../../.."
name=$1; workers=$2; shift 2
H=experiments/analysis/hard_map_training_20261021
D=experiments/compare/regeln
.venv/bin/python -m scripts.par_eval --weights agents/sherlock/weights/agent_p0.pth "$@" --opponents solution92 \
    --seed-list $H/dev_hard150.json --workers $workers --out $D/D21_${name}_hard150.csv 2>&1 | grep -v geladen
.venv/bin/python -m scripts.par_eval --weights agents/sherlock/weights/agent_p0.pth "$@" --opponents solution92 \
    --seed-list $H/dev_easy60.json --workers $workers --out $D/D21_${name}_easy60.csv 2>&1 | grep -v geladen
