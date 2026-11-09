# MATCH38 einmalig frisch bestätigen

## Zweck und Auswahl

Der abgeschlossene feste Screen nominiert MATCH38: Solution 37/40 statt V14 und CONTROL38 je 36/40, direkt 26/40 gegen V14 und 24/40 gegen Kontrolle. Alle vier vorher festgelegten Gates und unabhängige Nachrechnung bestanden. Die breiten Intervalle erlauben noch keine Übernahme. Geschlossener Ergebnisstand `82161f8`, Root-Abschluss SHA `574cc99f8b943eb68a805871c96fd6d9f6fd61c4ed42fa37872d5a7bc3d0f3f9`.

Eine begrenzte einmalige Bestätigung hat Vorrang vor einer neuen Trainingsidee. Der Nutzer autorisiert autonome Umsetzung und möchte überschaubare Tests. Die hier gewählten 440 Spiele ersetzen frühere unverbindliche 400-Spiel-Überlegungen **vor jeglichen neuen Daten**: 60 statt 40 direkte Karten verbessern die Präzision des primären Vergleichs. Kein optionaler Nachschlag.

## Unveränderte Kandidaten

- MATCH38 bleibt exakt die akzeptierte Evalkopie `experiments/analysis/match_weight_compare_20261109/technical_v1/match.pth`, SHA `ff66e696665019d304848ebf0e3b022fd1a1d08eaa9b25518f12f8c3e33e6a1b`.
- V14 bleibt die akzeptierte Evalkopie dort `v14.pth`, SHA `817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2`.
- Keine zusätzlichen Netze, Gradienten, Auswahl, Konfigurationsänderung oder Kalibrierung. Beide Kopien verwenden die gleiche normalisierte ursprüngliche Inferenzkonfiguration mit `frozen=False`. Originale Abgabe und ZIP bleiben geschützt.
- Bereits tatsächlich geprüfte Montage/Loader und 200 fehlerfreie Spiele werden historisch gebunden. Nicht erneut die alte Admission gegen einen neuen HEAD ausführen. Alle bisherigen gebundenen Quelldateien/Interpreter/Engine bleiben bytegleich; neue Bestätigungswerkzeuge dürfen hinzukommen. Ändert sich eine bisherige Runtimequelle, ist diese enge Aufnahme unzulässig.

## Feste Ausführungen

Panel: `solution92`, `default`, `sol92_sq`, `rush`, jeweils dieselben 20 neuen Karten und beide Seiten, je Modell 160 Spiele. V14 und MATCH38 parallel, jeweils ein bestehender `par_eval`-Worker. Danach MATCH38 direkt gegen die V14-Evalkopie auf 60 anderen neuen Karten, beide Seiten: 120 Spiele. Insgesamt genau **440**. Konkrete Bereiche stehen einmal im Implementierungsplan; begrenzten lokalen Kartencheck samt Lücken vor Aufnahme dokumentieren.

Keine zusätzliche technische Spielreihe notwendig: Modelle und gesamte bisherige Runtime sind dieselben. Neue Lauf-/Auswertungswerkzeuge synthetisch testen und unabhängig prüfen. Root nimmt diese eine Phase separat nach Quellencommit, frischer tatsächlicher Quota und Prozessprüfung auf. Keine automatische Übernahme, Wiederholung, Ersatzspiele oder Fortsetzung unvollständiger Reihen.

## Vor Daten feste Freigabekriterien

Alle folgenden Kriterien müssen erfüllt sein. Echte Siege sind `result == 1`; ein Remis ist kein Sieg. Scores für Mittelwerte und Intervalle zählen Remis als 0,5.

1. Direkt mindestens **72 echte Siege von 120** und untere deskriptive 95%-Ganzkarten-Scoregrenze **größer als 0,5**.
2. Panel mittlerer gepaarter Scorekontrast MATCH38 minus V14 **mindestens 0**, untere deskriptive 95%-Ganzkartengrenze **mindestens −0,025**.
3. Gegen Solution und default jeweils **mindestens so viele echte Siege wie V14**.
4. Gegen Square-Solution und rush jeweils **höchstens zwei echte Siege weniger als V14 von je 40 Spielen**.

Unveränderte Statistikhelfer: 5.000 PCG64-Seed-0-Resamples. Panel resampelt ganze Karten gemeinsam über alle vier Gegner und beide Seiten; direkt beide Seiten gemeinsam. Grenzvergleiche verwenden fest `1e-12` Rundungstoleranz, strikte Direktuntergrenze `> 0.5 + 1e-12`.

Die Direktprüfung ist primär. Die Panelbedingungen sind **empirische Stabilitäts- und Freigabekriterien**, kein formaler Beweis allgemeiner Nichtunterlegenheit innerhalb einer 2,5-pp-Marge. Bei identischen Kartenkontrasten degeneriert der Bootstrap; insbesondere `[0,0]` erfasst unbekannte Kartenrisiken nicht. Dies explizit kennzeichnen und alle absoluten W/D/L berichten. Keine Korrektur über historische Projektversuche, keine allgemeine 100%-Garantie und kein isolierter Kausalnachweis für das Matchreward. Ein Solution-Gleichstand ist kein Beweis einer Solution-Verbesserung.

## Entscheidung und Betrieb

Bei Fehlschlag bleibt V14, diese Bestätigung wird ohne Nachschlag geschlossen. Bei Bestehen ist nur die abgegrenzte Aussage eines frisch bestätigten Direktvorteils mit erfüllten empirischen Panelkriterien zulässig. Vor tatsächlichem Ersatz weiterhin alte Abgabe sichern, exakten Kandidaten reproduzieren, Kursinterface/erforderliche Laufzeit prüfen und neue Schutz-/Paket-Hashes dokumentieren. Bestehen allein überschreibt keine Gewichte.

Maximal zwei Modellworker, keine parallelen Tests. Quelle/HEAD/Eingaben während der Phase festhalten. Akkubetrieb und Restkontingent ausdrücklich erlaubt; echte Quota aktuell halten, Resets ausschließlich durch Moayed. Bei tatsächlichen 100 Prozent kontrolliert sichern. Mahmouds Änderungen am sicheren Übergang integrieren, fremde Dateien erhalten. Ergebnisse sinnvoll committen/pushen und Hauptkopie aktualisieren.
