# Zwei Vollschüler aus Lehrerbefehlen

Beide Netze lernen den vollständigen Befehl pro Einheit. Der erste Kopf wählt unter sechs Aktionen. Der zweite bewertet ein Schussziel auf der 24×24-Karte. Die Trainingsfrage lautet, wie sich zusätzliches Nachahmen tatsächlich vom starken Lehrer gespielter Stellungen auf denselben Schüler auswirkt.

| Woher die gespeicherte Stellung stammt | Lernkarten | Diagnosekarten | Lern-/Diagnosearchive |
| --- | ---: | ---: | ---: |
| V14 spielte, Kaggle-Platz 3 gab Schattenbefehle | 32 | 8 | 64 / 16 |
| V14 mit Bewegungsberater R1 spielte, derselbe Lehrer gab Schattenbefehle | 120 | 24 | 240 / 48 |
| Kaggle-Platz 3 spielte selbst gegen sich, V14 oder Solution | 216 | 24 | 304 / 33 |

Die Kontrolle lernt auf den ersten beiden Gruppen (152 Karten). Der zweite Schüler erhält zusätzlich die dritte Gruppe (368 Lernkarten). Beide werden auf allen 56 separaten Diagnosekarten geprüft. Für die 240 frischen Karten sind 240 Spiele angesetzt. Der vorab erzeugte Spielplan erwartet 337 Sitzarchive, weil der Collector bei den 97 Selbstspielen beide Lehrerperspektiven festhält. Der Datenbeleg wird mit den tatsächlich gesammelten Archiven verglichen. Die Lernkarten sind 7280000 bis einschließlich 7280215, die Diagnosekarten 7280216 bis 7280239. Die Gruppen enthalten 88/9 Selbstspiele, 68/6 Spiele gegen V14 und 60/9 gegen Solution. Auf einer Karte gehören beide Seiten immer zum selben Datenteil. In 11 Lernkarten und 3 Diagnosekarten des historischen V14/Kaggle-Vergleichs sind die kanonischen Nutzdaten beider Sitze laut Archiv identisch. Die Sitze bleiben in beiden Armen wie im historischen Datensatz enthalten.

Neuinitialisierung mit Seed 2711, 32 Kanäle, 3 Restblöcke, 128 versteckte Einheiten, 5 volle Epochen, AdamW und OneCycleLR mit maximaler Lernrate 0,001. Ein Batch gruppiert ganze Spielschritte mit durchschnittlich etwa 256 Einheitsentscheidungen. Pro ausführbarem Lehrerkommando zählt eine gewöhnliche Kreuzentropie; bei legalen Lehrerschüssen kommt die Ziel-Kreuzentropie mit Gewicht 0,5 hinzu. Der Schuss ist ab Energie ≥ Schusskosten erlaubt. Das eigene Feld ist ein zulässiges Ziel, wenn die Einheit schießen kann. Ziele außerhalb von Reichweite oder Karte gehen nicht ins Training ein. Der Schüler übernimmt keine Gewichte vom Kaggle-Agenten; die lokal trainierte Politik enthält nur ihre eigenen Parameter. V14 liefert seine Spielkonfiguration.

## Datensatz erstellen oder übernehmen

Bereits vorhandene Batches und Belege direkt verwenden. Die folgenden Bash-Befehle zeigen auch den Neuaufbau auf einem anderen Rechner. `W` bezeichnet den Trainingscheckout mit diesem Werkzeug, `C` einen Collector-Checkout auf Stand `565d8a216f9298f72b6191622ac14da06e9a55bb` mit dem offiziellen Kaggle-Release und den normalen V14-Gewichten. Python benötigt die Projektumgebung. Die historischen NPZ-Dateien aus den beiden genannten Ordnern müssen unter `D` liegen.

```bash
W="$PWD"
C=/pfad/zum/collector
D=/pfad/zum/hauptcheckout/experiments/imitation
T="$D/final_20261115_expert"
P="$W/experiments/analysis/full_student_20261115"
O="$D/final_20261115_whole_students"
PY=/pfad/zum/hauptcheckout/.venv/bin/python
mkdir -p "$O" "$P/collection"

# Nur bei vollständigem Neuaufbau. Vorhandene Läufe weiterverwenden.
(cd "$C" && "$PY" -m scripts.fetch_kaggle3)
for i in 0 1 2 3; do
  first=$((7280000 + 60*i))
  test ! -e "$T/batch$i" || exit 1
  (cd "$C" && "$PY" -m scripts.imitate collect --games 60 --workers 1 \
    --seed0 "$first" --mix 'kaggle3:0.4,v14:0.3,solution92:0.3' --out "$T/batch$i") || exit 1
  "$PY" -m scripts.full_student_study receipt --batch "$T/batch$i" --collector "$C" \
    --out "$P/collection/batch$i.json" || exit 1
done
```

Der Prüfschritt liest die veröffentlichten Byteprüfsummen aller 368 historischen Sitzarchive. Für die neuen Dateien prüft er pro Tranche die vorher festgelegten Karten, Sitze und Gegner, Quelldateien und Lehrergewichte, Einzelprüfsummen, Formate sowie die Zahl der Einheitsentscheidungen. Der Beleg einer Tranche bindet 41 Dateien von Sammler, Agent und Lehrer. Die separate Datei `collection/environment.json` hält die Konfiguration der Python-Umgebung und Prüfsummen der zehn Lux-Module fest. Die eingefrorene Datenliste ist zwischen Rechnern portabel, sobald dieselben Rohdaten und Belege vorliegen. Bei einer neuen Sammlung kann allein die gemessene Laufzeit im Beleg zu einem anderen Manifesthash führen.

```bash
args=(--v14 "$D/final_20261115_v14_advice" --mixed "$D/final_20261115_movement_dagger"
      --expert "$T" --receipts "$P/collection" --manifest "$P/corpus.json")
hash=$("$PY" -m scripts.full_student_study freeze "${args[@]}") || exit 1
for arm in historical plus_teacher; do
  "$PY" -u -m scripts.full_student_study fit "${args[@]}" --manifest-sha256 "$hash" \
    --arm "$arm" --device cpu --out "$O/$arm.pth" > "$O/$arm.log" || exit 1
done
```

Wenn das Manifest schon vorliegt, dessen dokumentierten SHA-256-Wert direkt an `fit` geben. Jeder Fit prüft die Eingaben erneut, setzt Pythons und NumPys globalen Zufallsgenerator sowie den Torch-Startseed und nutzt den plattenbasierten normalen Trainer. Gewichte der letzten Epoche werden unter einem neuen Dateinamen gespeichert. CPU-Einzelthread und dieselben Bibliotheksversionen dienen der Reproduktion. Bei Bedarf ist `--device mps` möglich; beide Arme auf demselben Gerät vergleichen.

## Diagnose und anschließender Vergleich

Pro Herkunft zeigt das Ende des Trainingslogs die Genauigkeit der sechs Aktionsklassen insgesamt und des vollständigen Befehls inklusive Schussziel. Die Checkpoint-Metadaten unter `full_policy_study.validation` enthalten zusätzlich die Zahl gültiger Lehrerschüsse, die exakte Zielquote und die Quote im Umkreis von einem Feld. Wird auf der größeren Datenmenge derselbe Anteil fünfmal gesehen, sind mehr Optimierungsschritte möglich; der Vergleich misst den Nutzen des gesamten zusätzlichen Trainings.

Für den vorgesehenen Vergleich lernt der Schüler den ganzen Befehl. Im Hybridmodus `points` steuert V14 den Halter auf einem bestätigten Punktefeld und Einheiten mit einem bestätigten Punktefeld als zugewiesenem Ziel. Bei den übrigen Einheiten gilt der vollständige Schülerbefehl. Beide Arme verwenden `imit_stay_bias=1.5` und `imit_unstack=true`. Nach beiden Fits liest die [Spielprüfung](SPIELPRUEFUNG.md) die exakten Validierungszähler aus den Checkpoints und prüft die Identität von Trainingsdaten und Quellen. Bei positivem Ergebnis spielen V14 und historische Kontrolle jeweils 64 externe Partien. Der neue Kandidat spielt 64 externe und 32 zusätzliche direkte Partien gegen V14.

Die Kartenliste darf keine Trainings- oder Diagnosekarte enthalten. Ein Vergleich auf derselben Liste wählt keine Einzelkarten, Sitze oder Entscheidungen nach Ergebnis aus. Eine spätere Übernahme verlangt eigene unabhängige Spielbelege und die normale Kursprüfung.

Das tatsächlich eingefrorene [Korpus](corpus.json) trägt SHA-256 `bd6744c9d4ac08eda6958e3dff637f257ac96b5ae8a3b6098238c4453a0bebea`. In der Lehrerkohorte sind 1.079.558 Lernentscheidungen und 114.893 Diagnoseentscheidungen enthalten.
