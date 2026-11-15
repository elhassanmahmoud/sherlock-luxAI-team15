# Wechsel zu V15 im dritten Match

Der [vorab festgelegte Auslöser](PLAN.md) erreichte alle vier ursprünglich verlorenen und zwölf ursprünglich gewonnene Solution-Partien. Genau diese 16 Sitze werden mit derselben Karte und Startseite einmal aus der Anfangsstellung gespielt. Bis zum ersten öffentlichen Rückstand ab Schritt 50 bei einem Matchstand von 1:1 gilt der vollständige Befehlssatz des ursprünglichen R3. Ab dem Zug, in dem Sherlock den Rückstand zum ersten Mal sieht, gilt der vollständige Befehlssatz von V15 bis zum Spielende. Auch ein späterer Ausgleich führt zu keiner Rückkehr.

Beide Agenten beobachten die Partie ab Zug null. Der Schattenagent erhält die tatsächlich ausgeführten Befehle über dieselbe Rückmeldung wie im früheren Vergleich. Vor dem Wechsel wird die Bewegungshistorie von V15 auf die R3-Befehle abgeglichen. Nach dem Wechsel verbucht V15 seine nativen Befehle und R3 erhält den von V15 ausgeführten Weltbefehl. Der Prof bekommt dadurch dieselben vollständigen Bewegungs- und Schussbefehle wie in der jeweiligen Originalpolitik.

## Belege pro Spiel

- Vor dem Auslösezug müssen alle 16 Befehle beider Spieler mit den historischen R3-Befehlen übereinstimmen. Dies umfasst die Zielkoordinaten jedes Schusses und wird für jede Startseite getrennt gehasht. Auch Solutions gleichzeitig abgegebener Befehl im Auslösezug muss noch identisch ausfallen.
- Globaler Zug, Matchschritt und beide öffentlichen Punktestände am ersten Wechsel müssen auf die Werte des bereits abgeschlossenen [Befehlsreplays](../r3_v4_wl_20261115/solution_scope/partien.tar.gz) führen. Die ersten beiden Matchausgänge einschließlich beider Punktsummen bleiben vollständig überprüfbar. Der Kandidat protokolliert ab wann eine lebende eigene Einheit wirklich einen anderen Befehl ausführte.
- Je Vergleichsdatei werden die Aktionsfolgen beider Spieler für alle 303 Züge, sämtliche drei offiziellen Matchgewinner, die Punkte beider Mannschaften und das Endergebnis gespeichert. Der Prüfer akzeptiert nur den zuvor versiegelten Vergleichssitz. Beim Wiederaufnehmen zählt er einen bereits gespeicherten gültigen Sitz genau einmal.

## Auswertung auf den 184 alten Karten

Die 352 übrigen Sitzresultate folgen dem belegten R3-Ausgang. In 322 Partien gewann R3 die ersten beiden Matches und schließlich 3:0. Weitere 29 reproduzierte R3-Kontrollen gewannen die ersten beiden Matches und verloren das dritte. Ein weiterer ursprünglicher 2:1-Sieg erreichte den offenen Matchstand, aber nie den definierten öffentlichen Punkterückstand. Ohne Umschaltzug bleibt der ursprüngliche Befehlsverlauf erhalten.

Die Auswertung weist gerettete und zusätzlich verlorene Spiele, Punkte und Matchsiege für die 16 Eingriffe und die 352 übernommenen Verläufe getrennt aus. Zur Schätzung des Unterschieds über alle 368 Spiele zieht sie 10.000-mal ganze Karten mitsamt beiden Startseiten (PCG64, Seed 2711). Ein positiver Nettozuwachs erlaubt lediglich die Planung eines eigenständigen Vergleichs auf neuen Karten. Der Prüfer startet ausschließlich den historischen Vergleich.

## Nachbauen

Der vollständige lokale Projektordner enthält die Modellgewichte, sechs frühere Kartenblöcke, das versiegelte Befehlsarchiv und die genau passende Spielumgebung. Die folgende Folge rekonstruiert die Version mit beiden historischen Forschungsagenten in einem neuen temporären Ordner. Das Verzeichnis mit den vorhandenen Eingaben wird nur gelesen. Als `REPLAY` den tatsächlich von `scripts.r3_m3_deficit_replay` geschriebenen JSON-Bericht angeben. Der erwartete SHA-256-Wert ist unten fest eingetragen.

```sh
PROJECT="$PWD"
RUN=$(mktemp -d)
git archive b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5 agents scripts lux | tar -x -C "$RUN"
for tool in r3_v4_contact_agent r3_v4_contact_study r3_v4_mixed_duel r3_v4_parent_source \
            r3_v4_wl_agent r3_v4_wl_games r3_v4_wl_plan r3_v4_wl_solution r3_v4_wl_solution_registry; do
    git show "d69ef43fd413bbff9fb83998d46b16aae49fdf1e:scripts/$tool.py" > "$RUN/scripts/$tool.py"
done
ln -s "$PROJECT/experiments" "$RUN/experiments"
cp scripts/r3_m3_deficit_agent.py scripts/r3_m3_deficit_games.py scripts/r3_m3_deficit_replay.py "$RUN/scripts/"
"$PROJECT/.venv/bin/python" -B "$RUN/scripts/r3_v4_parent_source.py" --repo "$PROJECT"
cd "$RUN"
REPLAY=/pfad/zum/assessment.json
REPLAY_SHA=ec3ce775afdb7536897385514649876d5c3a42be3868457921b1fe3d6a299b42
"$PROJECT/.venv/bin/python" -B -m scripts.r3_m3_deficit_games check --project "$PROJECT" --replay "$REPLAY" --replay-sha256 "$REPLAY_SHA" --out "$RUN/causal"
"$PROJECT/.venv/bin/python" -B -m scripts.r3_m3_deficit_games run --project "$PROJECT" --replay "$REPLAY" --replay-sha256 "$REPLAY_SHA" --out "$RUN/causal"
"$PROJECT/.venv/bin/python" -B -m scripts.r3_m3_deficit_games verify --project "$PROJECT" --replay "$REPLAY" --replay-sha256 "$REPLAY_SHA" --out "$RUN/causal"
```
