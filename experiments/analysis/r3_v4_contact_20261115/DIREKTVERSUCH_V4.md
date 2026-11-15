# Kontakt gegen V15 im direkten Duell

Der Kontaktagent gewann im abgeschlossenen Screen gegen Solution 32/32, gegen Kaggle 0/32 und direkt gegen V14 30/32. V15 gewann 32, 2 und 26 Spiele. Der allgemeine Screen der Kombination ist damit gescheitert. Hier ist ausschließlich die Frage registriert, wie häufig Kontakt gegen unmodifiziertes v4 mixed (V15) direkt gewinnt.

## Karten und Referenz

Seeds 7170000 bis einschließlich 7170023, Kontakt je einmal als player_0 und player_1. Diese 24 Karten stammen vollständig aus dem ersten Direktduell. Kein Karte- oder Sitzfilter. Im damaligen Duell gewann v4 gegen R3 36/48 Spiele und 100/144 Matches. Diese Resultate und beide echten Befehlsströme liegen schon vor. Die 48 neuen Spiele ersetzen nur den damaligen R3-Sitz durch Kontakt. Die Gegenüberstellung ist eine Beschreibung auf wiederverwendeten Karten.

## Durchführung

Arbeitsverzeichnis ist die Kopie des eingefrorenen Kontakt-Spiels. Sie enthält die ursprünglichen Git-Bäume von R3 und v4, das selektive R3-Modell und beide notwendigen Gewichte für v4. Das Argument `--project` zeigt auf den Hauptcheckout mit veröffentlichten Rohdaten und Git-Objekten. Beispiel für einen verfügbaren Worker aus dem Snapshot-Stamm:

```sh
P=/pfad/zum/Sherlock-Hauptcheckout
"$P/.venv/bin/python" -B -m scripts.r3_v4_contact_duel check --project "$P"
caffeinate -i "$P/.venv/bin/python" -B -u -m scripts.r3_v4_contact_duel run --project "$P"
"$P/.venv/bin/python" -B -m scripts.r3_v4_contact_duel assess --project "$P"
```

Der Vorabgleich bindet Git- und Modellherkunft, Spielumgebung, die vier veröffentlichten Dateien des alten Duells, den damaligen Spielablauf und alle 352 Kontakt-Screen-Partien. Kontakt nutzt den unveränderten damaligen Kontaktactor. Gegner ist der unveränderte Konstruktor des gemischten v4 mit Radius 5, Stay-Bias 1,5 und Unstack. Im öffentlichen Kursablauf erhalten beide Sitze 303 Updates zu ihren tatsächlich gespielten Weltbefehlen. Jedes Spiel wird einzeln und exklusiv unter `experiments/analysis/r3_v4_contact_20261115/direct_v4` gespeichert. Bereits fertige Sitze werden überprüft und übersprungen. Der Startprüfer meldet anderswo gefundene Direktduelle mit Kontakt und v4 im Ausgaberepo, bevor er ein Spiel startet.

## Ergebnisauswertung

Primär werden Kursgewinne aus drei offiziellen Matchentscheidungen einschließlich Tiebreak gezählt. `completed.json` enthält außerdem Kontakt- und v4-Matchsiege, Ergebnisse nach Sitz und Karte sowie die Zahl gegenüber dem früheren R3-Sitz hinzugewonnener und abgegebener Partien. Für 95%-Intervalle werden 10.000-mal ganze Karten mitsamt beiden Sitzen gezogen (PCG64, Seed 2711). Ein überzeugender Direktvorteil erfordert eine untere Grenze des Kontakt-Sieganteils über 50 %. Dieser Endpunkt betrifft ausschließlich das unmittelbare Duell. Ein künftiger Anspruch gegen Zielgegner würde eine separate Replikation erfordern. Der Runner hat keine Folgestufe.
