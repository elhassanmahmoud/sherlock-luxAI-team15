# Tatsächliche Auswahlabnahme — 03.11.2026

**PASS: Die vollständige Auswahl ist unabhängig akzeptiert. FT18 ist für die einzige frische Bestätigung nominiert. Noch keine Übernahmefreigabe.**

Alle13 Jobs sind complete/exit0 und alle8800 erwarteten Spiele vorhanden. Der unabhängige Auswerter hat vor jedem Datenzugriff vollständigen State und erfolgreiche Jobbelege verlangt. Exakte CSV-Schemata, alle Gegner/Seeds/Seiten ohne Duplikate oder Teilmengenschnitt,303 Schritte,v2, endliche Werte und konsistente1/0.5/0-Wertung bestanden. Freeze-/Planpins, Quellinventar/HEAD7c906e1, Interpreter-, Modell-, Protokoll- und Ergebnisdatei-Hashes stimmen; die eingefrorenen Quellen wurden nicht geändert.

Sämtliche Punkte, Zählungen, Whole-card-PCG64-Bootstrapintervalle (5000,Seed0,linear), Gates und die Nominierung stimmen mit der offiziellen Auswertung überein. Der vollständige rekursive Vergleich verwendet weiterhin strikte Schlüssel und maximal1e-12 numerische Rundungstoleranz. Nominierung basiert unabhängig auf exakten ganzzahligen Halbsiegen; ein realer Float-/Gleichstandskonflikt besteht hier nicht.

| Kandidat | Panel Δ pp | Solution Δ pp | Direktquote | Screen zugelassen |
|---|---:|---:|---:|---|
| PAIR18 | -5.1042 | -1.88 | 32.500% | nein |
| PAIR24 | -0.7292 | +2.50 | 52.500% | nein |
| FT18 | +0.9375 | +1.25 | 61.250% | ja |
| Z36 | +0.8333 | +1.25 | 50.000% | ja |
| C36 | -0.1042 | +1.25 | 47.500% | nein |
| R36 | -2.7083 | -4.38 | 53.125% | nein |

FT18: Panel **+0.9375pp**, Solution **+1.25pp**, default160/160, direkt98/160=**61.25%**. Alle vier Auswahlgates erfüllt. Z36 erfüllt ebenfalls seine Auswahlgates, liegt mit+0.8333pp im Panel jedoch strikt hinter FT18; Abstand+0.1041667pp, kein Gleichstand. C36 bleibt methodische Kontrolle und ist nie nominierbar. R36 verfehlt auch beide Kontrollvergleiche.

Die Paneldifferenz von FT18 hat ein95%-Intervall von **[-3.2292;+4.8984]pp**, enthält also0. Der Auswahlsieg ist kein gesicherter Stärkenachweis. Keine Auswahlkarten in die spätere Bestätigung poolen; kein Nachrücken oder zweiter Bestätigungsversuch nach einem Fehlschlag. Das lokale Panel und eine gepaarte Trainingsinitialisierung tragen keine allgemeine Aussage über unbekannte Battle-Gegner oder die Überlegenheit von Rettungs-Nachtraining.

Die Phase dauerte laut abgeschlossenem State18647.78s. Es wurden bei dieser Abnahme keine Modelle geladen, keine Spiele/Tests/Benchmarks ausgeführt und keine Quellen/Pläne/Weights/HEAD verändert.

## Offen dokumentierte Prüferkorrektur

Der erste externe Vergleich brach ausschließlich wegen eines Serializerfehlers des unabhängigen Prüfers ab: Das beschreibende Pflichtfeld opponent je Gegner fehlte in dessen erwarteter Ausgabe. Die eingefrorene Implementierung enthielt dieses Feld bereits. Ergänzt wurden der unabhängig bekannte Gegnername und ein synthetischer Schemafall; keine Statistik, Gates, Toleranzen oder Nominierung wurden verändert.20 kleine synthetische Prüfungen bestanden, anschließend der vollständige tatsächliche Vergleich. Alte Prüferfassung und ursprünglicher REJECTED-Report bleiben erhalten.

Maschinenabnahme: /tmp/sherlock-final-20261103/actual_review_v2.json
Aktueller Prüfer-SHA256: b530191b08376f3359e2f730bc813d714e68f1b529dbe90dabb7518579c1bfea
Offizielle Summary-SHA256: 39d5d5eb3e1ff15ae1276ce2341ff13a5ac8deaa6ab4eb177754695a153d4d46
