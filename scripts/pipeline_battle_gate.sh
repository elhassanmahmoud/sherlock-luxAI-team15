#!/bin/bash
# 29.10.2026: Auswahl und Bestaetigung nach docs/superpowers/plans/2026-10-29-battle-push.md.
#   bash scripts/pipeline_battle_gate.sh select  RUNDE NAME KANDIDAT.pth   (Auswahlblock, einmal je Kandidat)
#   bash scripts/pipeline_battle_gate.sh pick    RUNDE NAME1 NAME2 ...      (hoechstens ein Kandidat je Runde)
#   bash scripts/pipeline_battle_gate.sh confirm RUNDE NAME KANDIDAT.pth   (frischer Block, nur der gewaehlte)
# Kandidaten sind fertige .pth (Config eingebrannt, z. B. mit scripts.set_cfg), damit genau die geprueften
# Bytes uebernommen werden koennen. Hürden: scripts/league_gates.py. Log experiments/pipeline_battle_gate.log
# (kompatibel mit scripts/release_candidate.py: "Start NAME (" ... "GATE Bestaetigung: BESTANDEN").
# 30.10.2026: Referenz per Umgebung (REF = Gewichte, REFNAME = Dateikuerzel), Standard V10; Runde 3 gegen V11:
#   REF=experiments/releases/20261030_v11_baseline/agent_p0.pth REFNAME=V11 bash scripts/pipeline_battle_gate.sh ...
cd "$(dirname "$0")/.."
MODE=$1; ROUND=$2; shift 2
LOG=experiments/pipeline_battle_gate.log
PY=.venv/bin/python
D=experiments/compare/battle
W=${WORKERS:-12}
REF=${REF:-experiments/releases/20261022_v10_baseline/agent_p0.pth}
REFNAME=${REFNAME:-V10}
DIRECT=self:$REF
PANEL="solution92,sol92_sq,sol92_weak,self:experiments/releases/20261020_old3_sym3/agent_p0.pth,default"
case $ROUND in
    1) SEL=302000; SELDIR=302200; CONF=303000; CONFDIR=304000 ;;
    2) SEL=305000; SELDIR=305200; CONF=306000; CONFDIR=307000 ;;
    3) SEL=308000; SELDIR=308200; CONF=308400; CONFDIR=309200 ;;  # Reserveblock, nur nach Plan-Nachtrag
    4) SEL=310000; SELDIR=310200; CONF=310400; CONFDIR=311200 ;;  # Plan-Nachtrag 30.10., 18:31
    *) echo "Runde 1 bis 4"; exit 1 ;;
esac
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
run() {  # run WEIGHTS FIRST N OPPONENTS OUT
    [ -f "$5" ] && return 0
    $PY -m scripts.par_eval --weights "$1" --first $2 --n $3 --workers $W --opponents "$4" --out "$5" \
        2>&1 | grep -v geladen | tail -1 >> $LOG
}
sha() { shasum -a 256 "$1" | cut -c1-16; }

case $MODE in
select)
    NAME=$1; CAND=$2
    log "Auswahl Runde $ROUND: $NAME ($CAND, SHA-256 $(sha $CAND)), Referenz $REFNAME, Code $(git rev-parse --short HEAD)"
    run $REF $SEL 200 "$PANEL" $D/G${ROUND}_${REFNAME}_sel.csv
    run $CAND $SEL 200 "$PANEL" $D/G${ROUND}_${NAME}_sel.csv
    run $CAND $SELDIR 200 "$DIRECT" $D/G${ROUND}_${NAME}_seldir.csv
    $PY -m scripts.league_gates select $D/G${ROUND}_${REFNAME}_sel.csv $NAME $D/G${ROUND}_${NAME}_sel.csv \
        $D/G${ROUND}_${NAME}_seldir.csv --direct-opponent "$DIRECT" >> $LOG 2>&1
    log "Auswahl $NAME fertig"
    ;;
pick)
    ARGS=""
    for NAME in "$@"; do ARGS="$ARGS $NAME $D/G${ROUND}_${NAME}_sel.csv $D/G${ROUND}_${NAME}_seldir.csv"; done
    log "Wahl Runde $ROUND unter: $*"
    $PY -m scripts.league_gates select $D/G${ROUND}_${REFNAME}_sel.csv $ARGS --direct-opponent "$DIRECT" >> $LOG 2>&1
    tail -3 $LOG
    ;;
confirm)
    NAME=$1; CAND=$2
    other=$(ls $D/G${ROUND}_*_conf.csv 2>/dev/null | grep -v "_${REFNAME}_conf.csv" | grep -v "_${NAME}_conf.csv")
    [ -n "$other" ] && { echo "Runde $ROUND hat schon eine Bestaetigung: $other"; exit 1; }
    log "Start $NAME ($CAND, SHA-256 $(sha $CAND)), Bestaetigung Runde $ROUND, Referenz $REFNAME, Code $(git rev-parse --short HEAD)"
    run $REF $CONF 800 "$PANEL" $D/G${ROUND}_${REFNAME}_conf.csv
    run $CAND $CONF 800 "$PANEL" $D/G${ROUND}_${NAME}_conf.csv
    run $CAND $CONFDIR 400 "$DIRECT" $D/G${ROUND}_${NAME}_confdir.csv
    $PY -m scripts.league_gates confirm $D/G${ROUND}_${REFNAME}_conf.csv $D/G${ROUND}_${NAME}_conf.csv \
        $D/G${ROUND}_${NAME}_confdir.csv --direct-opponent "$DIRECT" >> $LOG 2>&1
    log "Ende $NAME"
    ;;
*)
    echo "Modus select, pick oder confirm"; exit 1 ;;
esac
