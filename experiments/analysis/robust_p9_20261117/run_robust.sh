#!/bin/bash
# Robustheit P9 gegen R3 (PLAN.md): beide Kurspakete gegen sechs weitere Spielweisen auf 7263000-7263024.
#   run_robust.sh FROZEN_DIR
set -u
FROZEN=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/robust_p9_20261117
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
P9ZIP=$MAIN/experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip
OPPS=default,random,rush,sol92_sq,dqn,self:agents/sherlock/weights/agent_p0.pth
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
shasum -a 256 $R3ZIP $P9ZIP agents/sherlock/weights/agent_p0.pth
run() { name=$1; w=$2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents "$OPPS" --seed-list $D/seeds_robust.json --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_robust "r3zip:$R3ZIP"
run p9_robust "r3zip:$P9ZIP"
log "ROBUST_DONE"
