#!/bin/bash
# Kandidaten-Gewichte aus experiments/candidates/ an die Originalpfade kopieren
# (experiments/ensembles/, experiments/ppo/cnn2|cnn3/ sind gitignored) und SHA-256 pruefen.
# Abgabe-Gewichte in agents/sherlock/weights/ werden NICHT angefasst.
#   bash scripts/install_candidates.sh
set -e
cd "$(dirname "$0")/.."
C=experiments/candidates
mkdir -p experiments/ensembles experiments/ppo/cnn2 experiments/ppo/cnn3
while read -r sha src dst; do
    [ -z "$sha" ] && continue
    if [ -e "$dst" ] && [ "$(shasum -a 256 "$dst" | cut -d' ' -f1)" != "$sha" ]; then
        echo "ABBRUCH: $dst existiert mit anderem Inhalt (nicht ueberschrieben)"; exit 1
    fi
    cp "$C/$src" "$dst"
    got=$(shasum -a 256 "$dst" | cut -d' ' -f1)
    if [ "$got" = "$sha" ]; then echo "OK   $dst"; else echo "FEHLER $dst: $got"; exit 1; fi
done <<'LIST'
3465225733bbbfbf05adc577f7af5f76cb2d886ff2ed895498434fac979ededd all18_v4.pth experiments/ensembles/all18_v4.pth
aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935 all18_v3.pth experiments/ensembles/all18_v3.pth
b2b7ffcc506d71a4657bb8990a71c0b25c4535f0f41564054ff687a1fa7b4607 all18_fo10.pth experiments/ensembles/all18_fo10.pth
e9ff09a64ae0327e49ea8a4c0810abcf47bf2f1b05db02a4f4a6c8266f868b03 all24fo.pth experiments/ensembles/all24fo.pth
007da1f1b040e54af61615ad817cf55cb8c025f6133a136a74f0fe9ca078d246 cnn2_ppo0040.pth experiments/ppo/cnn2/ppo_0040.pth
124ec118a55f9653483c8cf2b518f5af8a1d4dfedbbd154c74c3cd79ff95bf6a rules6.pth experiments/ensembles/rules6.pth
1879c991677f0c872768a19a904dd1cd4db66d71d811fdeae845e3e65f7f62a2 cnn3_bc.pth experiments/ppo/cnn3/bc.pth
5c16f62dbcdc0db563cb8684b3e4a8896c591867dc8e690d6e45f41d068b2e2e cnn3_ppo0050.pth experiments/ppo/cnn3/ppo_0050.pth
0efe4d39c8b2c8e56d4877e208b6064fc3766b9c486f83c6f82407cf11fb0bef cnn3_ppo0060.pth experiments/ppo/cnn3/ppo_0060.pth
LIST
echo "Fertig. Abgabe-Gewichte unveraendert:"
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
