# Fog-Nachtraining: Ergebnis des festen Vergleichs

**V14 bleibt.** Das normale Nachtraining liefert ein interessantes, aber noch nicht ausreichend belegtes Signal. Die Änderung des Nebelschuss-Rewards verbessert diesen Vergleich nicht. Beide Kandidaten verfehlen die vorab festgelegte Auswahlhürde; deshalb keine Bestätigung und keine zusätzlichen Spiele dieser Welle.

## Tatsächlich ausgeführt

Vier neue Einzelnetze ab derselben V14-Komponente18: zwei Zufallsstarts41/42, jeweils Kontrolle und Neutral. Je40 Vorlauf-,400 Lern- und32 Diagnosepartien; zusammen1888 Ausführungen und240000 Updates. Anschließend zwei feste38erEnsembles: unveränderte36Originalnetze plus jeweilige41/42-Endstände. Kein ausgewählter Zwischencheckpoint und keine veränderte Inferenzregel.

Die komplette Vorauswahl umfasst440 Partien in elfJobs, keine Remis oder fehlenden Ergebnisse. Gegen die drei externen Gegner:20 Karten7700000–7700019, jeweils beide Seiten. Direkte Duelle:20 separate Karten7700100–7700119, beide Seiten. Die vorab reservierten Bestätigungskarten wurden nicht verwendet. Mit den vier bekannten technischen Referenzausführungen ergeben sich2332 vollständige Ausführungen in dieser Fog-Studie; synthetische Tests sind keine Spiele.

| Modell | Solution92 | sol92_sq | default | Zweierpanel | Direkt gegen V14 |
|---|---:|---:|---:|---:|---:|
| V14 |37/40|37/40|40/40|74/80|–|
| CONTROL38 |38/40|37/40|40/40|75/80|28/40|
| NEUTRAL38 |37/40|36/40|40/40|73/80|26/40|

## Was sich daraus ableiten lässt

CONTROL38 erreicht direkt70%, mit gepaartem Karten-Bootstrapintervall[50%;90%]. Das ist ein positives Signal auf diesem kleinen Satz, kein gesicherter allgemeiner Vorsprung. Gegen Solution sind es95% statt92,5%; die Differenz beträgt+2,5 Prozentpunkte[0;7,5]. Im gemeinsamen Zweierpanel verbessert sich die Quote nur um+1,25pp[0;3,75]. Gefordert waren mindestens+2,5pp, also zwei zusätzliche volle Score-Siege auf80; tatsächlich ist es einer.

NEUTRAL38 erreicht direkt65%[45%;85%], im Panel aber−1,25pp[−3,75;0] gegenüberV14. Die vorab geplante gepaarte Neutral-minus-Kontrolle-Differenz beträgt−2,5pp[−6,25;0]. Damit gibt es bei diesen beiden Trainingsstarts und diesem Budget keinen Grund, die Reward-Neutralisierung zu übernehmen. Das beweist nicht, dass jeder Umgang mit unbekannten Treffern wirkungslos wäre.

Alle Intervalle resampeln ganze Karten einschließlich beider Seiten und Panelgegner,5000 Züge mit PCG64seed0. Sie sind unadjustiert;20 Karten und teilweise degenerierte Intervalle liefern begrenzte Sicherheit. Trainingsdiagnosen werden nicht in diese Zahlen gemischt. Weder diese Stichprobe noch40/40 gegendefault sind eine allgemeine100%-Garantie.

## Integrität und Entscheidung

Root45synthetische Tests bestanden, unabhängiger Code-/Methodenreview PASS. Tatsächliche Modelldateien wieder geladen, exakt36+2 geordnete Tensoren und ursprüngliche Inferenzkonfiguration geprüft. Der Vergleich lief vollständig unter Quellec096e4f0d1720900ee04d5acaa7faaef465fcded. Unabhängiger Rohdaten-/Statistikaudit:11Jobs/440Zeilen und280 Zahlen-/Strukturprüfungen PASS; `nominee:null` bestätigt. Alle eigenen Modell-/Wachhalteprozesse beendet.

Der erste Aufruf der Analyse mit relativen Pfaden scheiterte vor der Statistik an einem Pfadvergleich. Mit absoluten Pfaden wurde derselbe unveränderte Code erfolgreich ausgeführt; Rohdaten, Modelle und feste Regeln blieben gleich. Der enge CLI-Fix erfolgte erst nach historischer Abnahme, mit zwei zusätzlich bestandenen Regressionen. Keine Wiederholung von Spielen.

V14-P0/P1 SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Beide bleiben unverändert. Kandidaten und alle nachvollziehbaren Trainings-/Spielbelege sind experimentell archiviert. Die ursprünglichen Netze werden weder ersetzt noch neu gewichtet.

## Nächster begrenzter Schritt

Separat vorbereitete Offline-Diagnose mit vorhandenen Replaydaten: Wie oft verändern die neuen Netze den legalen Netzvorschlag, und wie groß ist ihr Beitrag zum Mittelwert? Höchstens10000 gespeicherte Folgezustände, keine neuen Spiele oder Lernupdates. Sie kann weder die Qualität einer Aktion noch die nachfolgenden Regeln bewerten. Erst anhand dieses Befunds einen neuen Ansatz ableiten; diese Auswahl wird nicht verlängert oder nachträglich umgedeutet.

## Nachweise

- `selection/summary.json`: vollständige Zahlen/Gates.
- `selection/*.csv`, `selection/receipts/*.json`: Rohdaten und Ausführung.
- `operations/selection-independent-audit.json` und `.md`: unabhängige Nachrechnung.
- `operations/historical_selection_acceptance.json`: Abschluss unter ursprünglichem Freeze.
- `../fog_reward_20261108/TRAININGSERGEBNIS.md`: Lernverfahren und ursprüngliche Trainingsabnahme.
