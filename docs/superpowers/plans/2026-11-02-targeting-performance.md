# P/PT: feste Leistungsstudie vom 02./03.11.2026

Vor den ersten Ergebnissen auf 841000/842000/843000 festgelegt.
V14-Referenz SHA-256 98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.
Ziel ist ein unabhängig bestätigter Fortschritt; 100 % gegen Solution ist ein Wunsch,
keine zugesicherte Eigenschaft auf allen zufälligen Karten.

## Kandidaten und Zulassung

- P: V14 mit genau `point_pair_swap=true` und `art_move_guard=true`; alle 36 Netze unverändert.
- PT: P, genau Komponenten18/19 aus `[q,*ensemble]` durch die beiden adaptierten
  End-q des festen Vierarmpiloten ersetzt. Andere34 Tensorzustände/Reihenfolge
  identisch, dieselbe Mittelung mit 1/36. Keine Kontrollnetze, keine Zwischenbesten.
- Alle vier Trainingsarme vollständig und unabhängig geprüft oder kein PT.
  Bekannte Validierungen wählen keinen Arm/Checkpoint. Kontrollarme bleiben Forschung.
- Vor Auswahl alle Quellen/HEAD, Protokolle, tatsächlichen Modellpfade und Hashes
  einschließlich Gegner eingefroren. Derselbe Freeze gilt für Bestätigung.
  Remote wird weiter abgerufen, Integration erst nach Abschluss.

## Festes lokales Panel

Sechs Gegner: `solution92`, `sol92_sq`, `self:experiments/releases/20261022_all18_v3/agent_p0.pth`,
`self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth`,
`self:experiments/releases/20261022_v10_baseline/agent_p0.pth`,
`self:experiments/releases/20261101_v13_neb/agent_p0.pth`.
`default` ist ein separater Sicherheitstest. Keine zufälligen Ersatzgegner und
keine Gleichsetzung dieses Panels mit Mahmouds historischer Sechserliga.
Technisch laufen alle sieben Gegner gemeinsam im vorhandenen Zwei-Worker-
`par_eval`; die Auswertung trennt das Sechsermittel von default. Kein eigener
serieller Default-Adapter: der bestehende Evaluator unterstützt DefaultAgent bereits.

## Auswahl: maximal ein Nominee

100 Karten841000–841099, beide Seiten, alle sieben Gegner für V14/P/PT:
je1400 Spiele. P und PT zusätzlich je200 direkte Spiele gegen V14 auf denselben
100 Karten. Gesamt4600. Wenn PT vor allen frischen Ergebnissen wegen fehlender
Zulassung entfällt, den kleineren Plan vorab gesondert fixieren; keine spätere Ergänzung.

Alle Auswahlbedingungen gemeinsam: Panelmittel-Delta mindestens+0,5Prozentpunkte;
Solution-Delta mindestens0; default mindestens99%; direkt mindestens50%.
Unter Zulässigen größtes Panel-Delta, bei Gleichstand innerhalb1e-9 einfacheres P.
Maximal ein Nominee; keiner bei verfehlten Bedingungen.

### Vorab erlaubter P-only-Fallback

Wenn der Vierarmpilot aus Ressourcen-/Zeitgründen unvollständig bleibt, darf
Root **vor dem ersten841er-Ergebnis** ausschließlichP als Kandidaten festlegen.
Das gemeinsame unveränderliche Freeze enthält dann genau baseline/P; sonst
baseline/P/PT. Ein nachträgliches Hinzufügen vonPT und ein Nachrücken bleiben verboten.
P benötigt keinen Trainingsaudit, weil sämtliche36Netze aus dem exakt gehashten
V14 stammen; geordnete Tensoridentität und ausschließlich2neueConfigflags sind
unabhängig zu belegen. PT benötigt weiterhin allevierACCEPTED-Arme.

P-only-Auswahl: dieselben100Karten/beidenSeiten/Gegner/Gates,1400Referenz+
1400P+200direkt=**3000Spiele**. Bestätigung unverändert9000Spiele/300Karten und
dieselben Gates. Keine Verkleinerung nach Ergebnissen. Initial136,32minAuswahl+
408,96minBestätigung+60minSchluss=605,28min; spätester Auswahlstart19:24:43Berlin
(konservativ19:24), Bestätigung weiter21:41. Akku-/Zeit-/Kontingentgrenzen gelten identisch.
Die reine Werkzeugunterstützung entscheidet noch keine Route und startet keine Spiele.

## Einmalige frische Bestätigung

300 Karten842000–842299, beide Seiten, sieben Gegner für V14 und den einzigen
Nominee: je4200 Spiele. Direkter Vergleich600Spiele auf getrennten300Karten
843000–843299. Gesamt9000. Nur nach vollständiger Auswahlabnahme beginnen.

Alle Übernahmebedingungen gemeinsam:

1. Panel-Delta mindestens+1,0pp und untere95%-Grenze strikt über0.
2. Solution-Delta mindestens0 und untere95%-Grenze mindestens−1,0pp.
3. default mindestens99% und Delta mindestens−1,0pp.
4. Direktquote: untere95%-Grenze strikt über50%.

Gleiche Karte als Cluster: beide Seiten und beim Panel alle sechs Gegner zusammen.
Gepaarter Karten-Bootstrap,5000Ziehungen, RNG0, Perzentile2,5/97,5.
Siegwertung1/0,5/0; neben dieser Quote reine Siege/Remis/Niederlagen nennen.
Numerische Toleranz1e-9 bei Grenzvergleichen; kein unverändertes `league_gates.pick`
oder dessen alte Panel-/Schwellenkonstanten verwenden.
Kein Nachrücken, keine Teilmengenauswahl, keine Stichprobenvergrößerung oder
Schwellenänderung nach Ergebnissen. Eine fehlgeschlagene Bestätigung beendet diese Studie.

## Daten, Ressourcen und Schluss

Jede Pflichtdatei vollständig: exakte eindeutige(seed,side,opponent)-Schlüssel,
303Schritte, Punktzählungv2, endliche/konsistente Kennzahlen, echte Quellen-/Gewichtshashes,
fehlerfreie Prozessausgänge; getrennte unabhängige Datenabnahme und Reproduktion.
Auswahl/Bestätigung erst nach vollständigen Phase lesen, nicht laufend nach Nominee suchen.
Mindestens30%Codex-Kontingent erhalten, kein Reset; ab35%Rest Abschlussreserve.
Maximalzwei schwere Worker. Nutzer erlaubt Akkuarbeit: unter35%keine neue lange Phase,
bei25%aktive eigene schwere Jobs stoppen. AC hebt diese Akkuschwellen auf.

Vor jeder Phase vollständige Laufzeit mit konservativem realem Durchsatz+20%Reserve
projizieren, einschließlich noch ausstehender Bestätigung und60minSchlussreserve
bis03.11.05:30Berlin. Zwei feste Laufzeitklassen: gemeinsamer Siebenervergleich
initial2,22Wallsekunden/Spiel, Direktduell initial3,0. Beide bei2Workern bereits
Wandzeit/Spiel, niemals erneut durch2teilen. Alte komplette Phasereceipts belegen
gemischteJobs maximal2,1952 und Direktjobs maximal2,9848; initial aufgerundet.
JeKlasse alle beobachteten Jobraten behalten; globaler Verlangsamungsfaktor ist
max(1, beobachteteRate/Initialrate der jeweiligenKlasse). Effektive Klassenrate
max(beobachtetesKlassenmaximum, Initialrate×globalerFaktor), dann feste verbleibende
Klassenmengen gewichten und20%addieren. Auswahl4200gemischte+400direkte,
Bestätigung8400gemischte+600direkteSpiele. Kein nachträgliches Optimieren an Ergebnissen.
Daraus initial210,48minAuswahl/408,96minBestätigung: Auswahl spätestens02.11.18:10:34Berlin
und Bestätigung spätestens21:41:02Berlin, sofern neuer Durchsatz nicht langsamer ist.
Vor Beginn neue Messung prüfen. Klassen statt unpassendem teuerstem Einzelkostensatz
auf alle Gegner vor sämtlichen841er-Ergebnissen unabhängig methodisch geprüft.
Keine lange Phase nach03.11.05:00Berlin beginnen; Nutzerende06:00Berlin verbindlich.

Nur bei qualifiziertem Kandidaten: V14-Sicherung erhalten, Kurs-Runner und sauberes
Runtime-ZIP prüfen, tatsächliche Hashes/Restaurierung dokumentieren, dann gezielte Übernahme.
Sonst V14 unverändert erhalten. Keine Moodle-Abgabe oder Präsentationsänderung in diesem Auftrag.
