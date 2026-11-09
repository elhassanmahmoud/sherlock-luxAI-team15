# Feste Auswahl der Ensemble-Verhaltensnetze

Die bereits vor Trainingsdaten festgelegte Auswahl aus `2026-11-09-ensemble-behavior.md` wird ohne Änderungen umgesetzt. Voraussetzung ist der tatsächliche vollständige, unabhängige und durch Root versiegelte Trainingsabschluss. Diese Datei startet keine Phase.

## Modelle und Frage

BEHAVIOR38 enthält die ursprünglichen 36 V14-Mitglieder in Originalreihenfolge, danach die beiden vollständigen ON-Endnetze aus Start 48 und 49. Im Training ersetzte das laufende eigene Netz Mitglied 18; die spätere Evaluation hängt beide Endnetze an die unveränderten ursprünglichen 36 an. Normaler Agent, keine Behavior-Hooks, dieselbe ursprüngliche Inferenzkonfiguration. Keine Auswahl zwischen den zwei Endnetzen, Skalierung oder weitere Mischung.

V14 und CONTROL38 werden als unveränderte bereits akzeptierte Evalkopien wiederverwendet. CONTROL38 enthält die beiden festen historischen Kontrollendnetze 48/49. Historische Kontrollen sind keine frisch trainierten unabhängigen Wiederholungen; alte vollständige Bibliotheks-/RNG-Snapshots fehlen. Aktuelle Quellen und ursprüngliche Quellenuntermenge sowie tatsächliche Modelle werden gebunden; nicht eine alte Admission gegen einen neuen HEAD ausführen.

## Getrennte Phasen und vorab feste Entscheidung

Zuerst eine tatsächliche Montage-/Loaderaufnahme mit null Spielen: alle drei Modellreihenfolgen, Tensoren, Dimensionen und Config prüfen. Nur BEHAVIOR38 muss neu serialisiert werden. Originaler Loader und vorhandene Prüfhilfen, keine neue Agentenlogik. Root und unabhängige tatsächliche Abnahme vor Performance.

Danach separat genau fünf 40er-Jobs (je 20 Karten, beide Seiten):

| Job | Vergleich | Karten |
|---|---|---|
| v14_solution | V14 gegen Solution | 9990000–9990019 |
| control_solution | CONTROL38 gegen Solution | 9990000–9990019 |
| behavior_solution | BEHAVIOR38 gegen Solution | 9990000–9990019 |
| behavior_v14 | BEHAVIOR38 gegen V14 | 9990100–9990119 |
| behavior_control | BEHAVIOR38 gegen CONTROL38 | 9990200–9990219 |

Genau vier Gates: BEHAVIOR38 hat mindestens so viele tatsächliche Solution-Siege wie V14 und mindestens so viele wie CONTROL38; direkt gewinnt BEHAVIOR38 mindestens 24 von 40 gegen jede Referenz. Unentschieden zählen nicht als Siege. Die Gates werden nicht nach Daten verändert. Bestehen bedeutet ausschließlich Nominierung, danach getrennte vorher festgelegte frische Bestätigung. Kein automatischer Gewichtswechsel, Nachschlag oder weiterer Kandidat.

Statistik: vorhandene Auswerter, 5.000 PCG64-Seed-0-Bootstrapziehungen ganzer Karten inklusive beider Seiten, 95%-Intervalle und beschreibender Score mit Remis=0,5. Rohdaten vorher auf exakt alle erwarteten 40 eindeutigen Keys, korrekte Gegner, beide Seiten, 303 Schritte, Punktzählung v2 und korrekte Ergebnisarithmetik prüfen. Keine fehlenden Karten durch Schnittmengen verstecken. Degenerierte Intervalle und unbehandelte wiederholte Auswahl offen nennen; keine allgemeine 100%-Behauptung.

## Betrieb

Profil `ensemble_behavior_compare_20261109`. Quellencommit und getrennte Aufnahme je Phase. Originale Schutzdateien unverändert. Maximal zwei Modellworker, fünf Jobs in Wellen, keine Tests parallel. Aktuelle echte Quota; Batterie und Restkontingent erlaubt, Resets nur durch Nutzer. Exklusive Pfade, korrekte Original-PID/PGID-Eigentümerschaft, kontrollierter eigener Fehlerstopp, keine automatischen Wiederholungen. Vorhandene einmalige Seedprüfung samt Grenzen wiederverwenden; keine neue breite Kartenjagd.
