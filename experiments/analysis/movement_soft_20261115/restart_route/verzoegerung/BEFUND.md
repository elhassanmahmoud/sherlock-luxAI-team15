# Kalibrierte Wartezeit nach dem Matchwechsel

**Die erste zulässige Routenentscheidung liegt bei öffentlichem Matchschritt 13.** Der vorab definierte Median des ersten öffentlich positiven V14-Punktestands beträgt 12,5. Bei Schritt 12 gilt der normale R3-Befehl. Bei Schritt 13 mit weiterhin null eigenen Punkten darf die bestehende Ziel- und Wegedistanzprüfung eingreifen. Beim ersten positiven Stand endet ihr Fenster für dieses Match. [Vor der Auswertung versiegeltes Protokoll](KALIBRIERPLAN.md)

| Historische V14-Partien gegen Solution | Matches | Davon gewonnen | Median erster öffentlich sichtbarer eigener Punkt bei Sieg |
|---|---:|---:|---:|
| M2 und M3 | 52 | 48 | **12,5** |
| M2 | 26 | 23 | 11 |
| M3 | 26 | 25 | 13 |
| Spieler 0, M2 und M3 | 26 | 25 | 13 |
| Spieler 1, M2 und M3 | 26 | 23 | 12 |

Der Median verwendet alle 48 tatsächlichen Matchsiege. Die mittleren Beobachtungen sind 12 und 13. Alle 52 Matchreihen enthalten die vollständigen öffentlichen Schritte 1 bis 100. Kein gewonnener Match war zeitlich zensiert. Die beiden Sitze und späteren Matches einer Karte sind abhängig. Die 13 Kartenmediane reichen von 3 bis 23. Die Kalibrierung beschreibt die frühere V14-Startzeit gegen Solution. Die Daten gehörten zur Entwicklung der Schüler. Die Karten waren für diesen Zeitvergleich unabhängig von den beiden Routenfällen vorab festgelegt. Eine Wirkung des verzögerten Eingriffs wurde hier nicht gemessen. [Alle 52 Matchzeilen](auswertung/matches.csv) · [Zähler und Aufteilung je Karte](auswertung/ergebnis.json)

## Abgleich mit den beiden bekannten Fällen nach der Kalibrierung

Auf 7273148/P0 traf die sofortige Route in M2 ausschließlich bei den Befehlen 17 und 18 eine andere Entscheidung als der normale R3 auf der jeweils erreichten Stellung. Beide liegen nach der kalibrierten Freigabe. In der Referenzfolge waren M1 und M2 bereits gewonnen. Bei ansonsten deterministisch identischen Abläufen ist daher für die verzögerte Variante derselbe Spielgewinn vor M3 zu erwarten. Im dritten Match würden die unmittelbaren Eingriffe auf dessen bisherigem Pfad bei 10 und 11 entfallen.

Auf 7273105/P0 käme der erste tatsächliche Unterschied des schnellen Routenlaufs an M2-Schritt 4 zu früh. Auf dem bis zum Umschalten maßgeblichen R3-Pfad gibt es jedoch schon bei M2-Schritt 13 eine zulässige Routenentscheidung für UID 3. Der normale R3 erhielt dort seinen ersten Punkt mit dem Befehl an Schritt 14. Der verzögerte Arm kann also bereits vor diesem Punkt von ihm abweichen. Ob dieser frühere Sieg zurückkehrt, ist offen. Auf beiden Karten sind alle Aussagen über die verzögerte Variante bislang Folgerungen aus den vorhandenen Abläufen. Die eigentlichen Vergleiche müssen die zwei früheren Versionen und den verzögerten Arm getrennt ausweisen.

Die alte Routenmessung nennt als ersten Punkt die Nummer des **eingereichten Befehls**, der im Folgezustand einen Punkt erzeugt. Die Kalibrierung verwendet die Nummer der öffentlichen **Eingangsbeobachtung**, bei der der Punkt vor der Entscheidung erstmals erkennbar ist. Innerhalb eines Matches unterscheiden sich diese Nummern um eins. Für 7273148/P0 M2 entsprechen die bisherigen 40 und 20 also den öffentlichen Schritten 41 und 21. Für 7273105/P0 M2 entsprechen R3s 14 dem öffentlichen Schritt 15. Am letzten Übergang wird der öffentliche Stand direkt zurückgesetzt. [Bisherige Route](../../../../../scripts/r3_restart_route.py) · [Zähler der früheren Routenläufe](../../../../../scripts/r3_restart_study.py)

## Quellen und Wiederholung

Die Originalserie umfasst alle Gegner aus der festen Dreierrotation. Für die Kalibrierung stammen alle Solution-Karten aus dem Bereich 7271000–7271039. Die 26 verwendeten NPZ sind im ursprünglichen Audit einzeln mit SHA-256 gebunden. Der Code prüft Dateihashes, Sitz, 303 Schritte, Protokoll, chronologische Reihenfolge, Matchuhr und identischen Teamstand aller Einheiten einer Beobachtung. Der Matchgewinner kommt aus der Differenz der öffentlichen Matchsiege (für M3 mit terminalem Endstand). Dies berücksichtigt auch Punkte-, Energie- und Zufallsentscheide. Das bei 200 Punkten gesättigte Eingangsmerkmal 10 unterscheidet null und positiv eindeutig. [Archivprotokoll](../../../combat_advice_20261115/data_protocol.json) · [Originalaudit](../../../combat_advice_20261115/v14_advice_audit.json)

Die älteren vier Dateien timing_sol92_*.csv stammen aus einem Sechserensemble ohne Punktversionsspalte. Der 1.-November-Verlustdatensatz und die V14-Fenster vom 15. November waren nach Verlust-/Schutzfällen angereichert. Die früheren R3-Folgeergebnisse auf 72731xx gehören zur Entwicklung der Fragestellung. Die vorhandene V14-Serie mit fester Rotation und identischen Gewichten lieferte die Kalibrierung ohne neue Partien.

Offline-Reproduktion mit einem Checkout, das die gesammelten NPZ unter experiments/imitation/final_20261115_v14_advice und das versionierte Audit enthält. AUSGABE muss ein neuer Ordner sein.

```bash
python kalibrieren.py --repo "$CHECKOUT" --out "$AUSGABE"
```

Die Kontrollpartien auf den sieben bekannten Karten und der vorgeschlagene spätere Vergleich auf 7285000–7285059 sind im Kalibrierprotokoll festgelegt. In den vorliegenden Studienplänen fand sich keine vorherige Belegung dieses frischen Blocks. Die laufenden unveränderten Studien haben weiterhin Vorrang.

## Gezielter 14-Sitze-Vergleich

Der Runner verwendet das eingefrorene Ausführungsverzeichnis der bestehenden Routenstudie plus zwei zusätzliche Module. Die Abgabequellen sind davon unabhängig. Mit P als absolutem Verzeichnis movement_soft_20261115, R3 als zugehörigem r3_soft.pth und NEU als neuem Ergebnisordner:

```bash
"$PY" -B -m scripts.r3_delay_study --study "$P" --r3 "$R3" --check
caffeinate -i "$PY" -B -u -m scripts.r3_delay_study --study "$P" --r3 "$R3" --out "$NEU"
```

Die reine Eingangsprüfung hat alle 14 archivierten R3-/Sofortroutenpaare bestätigt. Für zwölf Sitzschlüssel liegen beide vollständigen Befehlsverläufe vor; für 7273105/p0 und p1 enthält die getrennte, gehashte Reproduktion die ursprünglichen Endstände, Zwischenstände, UID-bezogene Gelegenheiten, den gemeinsamen Präfix und die Prüfsummen der vollständigen Verläufe. Für diese beiden Sitze lässt sich ein historischer Einzelbefehl nur an aufgezeichneten Gelegenheiten prüfen. Ein neuer verzögerter Verlauf wird pro Sitz als vollständiges NPZ mit beiden Spielern gespeichert. Die Auswertung benennt die Belegform pro Sitz und weist alle Rückfälle separat gegenüber R3 und gegenüber der Sofortroute aus. [Einzige Policyänderung](../../../../../scripts/r3_delay_route.py) · [Lauf und Prüfung](../../../../../scripts/r3_delay_study.py)
