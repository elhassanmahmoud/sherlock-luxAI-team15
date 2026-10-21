#!/bin/bash
# 21.10.2026 abends: Auswahlmessung fuer die Gefahr-Merkmale nach festem Plan
# (docs/superpowers/plans/2026-10-21-threat-features.md). Wartet auf die 6 Laeufe
# 20261021_full_rules_v3_threat_s40-s45_sol70, baut threat6 (nur neue Netze) und mix24
# (threat6 + 18 V3-Netze, --mixed) und misst V3, v3nets6 (Kontrolle), threat6, mix24 auf
# dem Auswahlblock 503 220-503 419 (200 Karten, beide Seiten, default + Solution_92).
# Frische Bestaetigungsbloecke werden hier NICHT benutzt. Abgabe-Gewichte unberuehrt.
# Log: experiments/pipeline_threat.log
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_threat.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
RUNS=experiments/runs/20261021_full_rules_v3_threat_s4
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
ev() { name=$1; w=$2
    [ -f $D/$name.csv ] || $PY -m scripts.par_eval --weights $w --first 3220 --n 200 --workers 6 \
        --out $D/$name.csv 2>&1 | grep -v geladen >> $LOG; }
cmp() { $PY -m scripts.compare_report --ref $D/$1.csv $D/$2.csv 2>&1 | grep -E "default |solution92" >> $LOG; }

log "Start, warte auf 6 Trainingslaeufe"
until [ "$(grep -l 'Fertig in' ${RUNS}[0-5]_sol70/log.txt 2>/dev/null | wc -l | tr -d ' ')" = "6" ]; do
    sleep 120
done
log "Training fertig"
W=""
for s in 0 1 2 3 4 5; do W="$W ${RUNS}${s}_sol70/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/threat6.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --mixed --out $E/mix24.pth $W $E/all18_v3.pth >> $LOG 2>&1
shasum -a 256 $E/threat6.pth $E/mix24.pth agents/sherlock/weights/agent_p0.pth >> $LOG
ev T21_v3_3220 $E/all18_v3.pth
ev T21_v3nets6_3220 $E/v3nets6.pth
ev T21_threat6_3220 $E/threat6.pth
ev T21_mix24_3220 $E/mix24.pth
log "Vergleich gegen V3"
cmp T21_v3_3220 T21_v3nets6_3220
cmp T21_v3_3220 T21_threat6_3220
cmp T21_v3_3220 T21_mix24_3220
log "Methodenfrage: threat6 gegen Kontrolle v3nets6"
cmp T21_v3nets6_3220 T21_threat6_3220
log "Ende"
