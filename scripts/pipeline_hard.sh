#!/bin/bash
# 21.10.2026 abends: Auswahlmessung fuer die schweren Karten (Prioritized Level Replay) nach festem Plan
# (docs/superpowers/plans/2026-10-21-hard-map-training.md). Wartet auf die 6 Laeufe
# 20261021_full_rules_v3_s40-s45_hard, baut hard6 (nur neue Netze) und hard24
# (hard6 + 18 V3-Netze, --mixed) und misst V3, v3nets6 (Kontrolle), hard6, hard24 auf
# dem Auswahlblock 503 820-504 019 (200 Karten, beide Seiten, default + Solution_92).
# Frische Bestaetigungsbloecke werden hier NICHT benutzt. Abgabe-Gewichte unberuehrt.
# Log: experiments/pipeline_hard.log
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_hard.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
RUNS=experiments/runs/20261021_full_rules_v3_s4
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
ev() { name=$1; w=$2
    [ -f $D/$name.csv ] || $PY -m scripts.par_eval --weights $w --first 3820 --n 200 --workers 6 \
        --out $D/$name.csv 2>&1 | grep -v geladen >> $LOG; }
cmp() { $PY -m scripts.compare_report --ref $D/$1.csv $D/$2.csv 2>&1 | grep -E "default |solution92" >> $LOG; }

log "Start: Referenzen V3 und Kontrolle zuerst (haengen nicht vom Training ab)"
ev P21_v3_3820 $E/all18_v3.pth
ev P21_v3nets6_3820 $E/v3nets6.pth
log "warte auf 6 Trainingslaeufe"
until [ "$(grep -l 'Fertig in' ${RUNS}[0-5]_hard/log.txt 2>/dev/null | wc -l | tr -d ' ')" = "6" ]; do
    sleep 120
done
log "Training fertig"
W=""
for s in 0 1 2 3 4 5; do W="$W ${RUNS}${s}_hard/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/hard6.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --mixed --out $E/hard24.pth $W $E/all18_v3.pth >> $LOG 2>&1
shasum -a 256 $E/hard6.pth $E/hard24.pth agents/sherlock/weights/agent_p0.pth >> $LOG
ev P21_hard6_3820 $E/hard6.pth
ev P21_hard24_3820 $E/hard24.pth
log "Vergleich gegen V3"
cmp P21_v3_3820 P21_v3nets6_3820
cmp P21_v3_3820 P21_hard6_3820
cmp P21_v3_3820 P21_hard24_3820
log "Methodenfrage: hard6 gegen Kontrolle v3nets6"
cmp P21_v3nets6_3820 P21_hard6_3820
log "Ende"
