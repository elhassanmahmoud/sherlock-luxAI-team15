#!/bin/bash
# 29.10.2026, 23:55: Morgen-Screen nach der RL-Liga (Plan docs/superpowers/plans/2026-10-29-battle-push.md,
# Nachtrag 29.10., 23:55). Nur Entwicklung auf Dev A, keine Auswahl und keine Uebernahme.
# 1. wartet auf das Ende von Runde 3 (dann sind 6 Kerne frei) und misst V10 und mix36 gegen die
#    zurueckgehaltenen RL-Gegner
# 2. wartet auf das Ende der RL-Liga, baut mixrl36 (V10 + ftrl18) und mixrl54 (V10 + ft18 + ftrl18) mit V10-Config
# 3. Screen beider mit scripts/battle_screen.sh
#   bash scripts/pipeline_battle_morning.sh      (WORKERS=6 neben Auswahl/Bestaetigung)
cd "$(dirname "$0")/.."
PY=.venv/bin/python
E=experiments/ensembles
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
LOG=experiments/battle_dev.log
export WORKERS=${WORKERS:-6}
until grep -q "Ende Runde 3" experiments/pipeline_battle_ft3.log 2>/dev/null; do sleep 60; done
echo "[$(date '+%d.%m. %H:%M')] Morgen-Screen: Start (Runde 3 fertig)" >> $LOG
bash scripts/battle_screen.sh V10
bash scripts/battle_screen.sh mix36 $E/battle_mix36.pth
until grep -q "Ende RL-Liga" experiments/pipeline_battle_ftrl.log 2>/dev/null; do sleep 60; done
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mixrl36.pth $V10 $E/battle_ftrl18.pth >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mixrl54.pth $V10 $E/battle_ft18.pth $E/battle_ftrl18.pth >> $LOG 2>&1
bash scripts/battle_screen.sh mixrl36 $E/battle_mixrl36.pth
bash scripts/battle_screen.sh mixrl54 $E/battle_mixrl54.pth
echo "[$(date '+%d.%m. %H:%M')] Morgen-Screen fertig" >> $LOG
