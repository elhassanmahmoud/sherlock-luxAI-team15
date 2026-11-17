# Frische Bestätigung "R3 + Schüler" auf 7159000–7159399 (festgelegt am 17.11.2026, 09:08, vor dem ersten Spiel)

**Freigabe:** Mahmoud hat die Bestätigung am 17.11. gegen 09:06 freigegeben („ja mach das, wir brauchen Fortschritt“).
Die Karten 7159000–7159399 sind seine Reservierung. Abweichend vom [Testplan](PLAN.md), der für die Bestätigung ein
Ja von Mahmoud und Moayed vorsah, läuft sie deshalb auf Mahmouds Ja allein. **Ob R3 als Abgabe ersetzt wird,
entscheiden weiterhin Mahmoud und Moayed gemeinsam.** Bis dahin bleibt R3 die Abgabe.

## Welche Variante antritt (festgelegt, bevor die zweite Prüfung fertig war)

Unter den Varianten, die auch die [zweite Prüfung](PLAN.md#zweite-prüfung-festgelegt-am-17112026-0832-vor-dem-ersten-spiel-auf-diesen-karten)
bestehen, tritt die mit dem höchsten gepaarten Punkteanteil gegen Kaggle auf der zweiten Prüfung an. Liegt SCHUELER
(ohne Taktiken) höchstens 0,5 Prozentpunkte unter SCHUELER_ALLE, tritt die einfachere Variante SCHUELER an. HYB_ENS8
baut auf V14 statt auf R3 auf und tritt nur an, wenn keine R3-Variante besteht. Die gewählte Variante und die
Prüfsumme ihres Kurspakets werden vor dem ersten Spiel als Nachtrag unten eingetragen.

## Was gespielt wird

- **Gespielt wird das echte Kurspaket**, gebaut mit `scripts/build_r3t_package.py` aus der eingefrorenen Quelle, als
  `r3zip:` geladen wie R3 selbst. Daneben das unveränderte R3-Paket (SHA-256 `8aabdc73…a64d`).
- Karten 7159000–7159399, beide Seiten, gegen Solution und Kaggle: je Agent 1.600 Spiele.
- Nur zur Information: direkt gegen R3 auf 7159000–7159099 (200 Spiele).
- 10 Prozesse, streng nacheinander ([Skript](run_bestaetigung.sh)).

## Vorab festgelegte Regel (alle Bedingungen müssen erfüllt sein)

Gepaart nach Karte gegen R3 (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze.py)):

1. **Punkteanteil gegen Kaggle:** Mittel mindestens +2,0 Prozentpunkte und untere 95-%-Grenze über 0.
2. **Gewonnene Spiele gegen Solution und Kaggle zusammen:** Mittel mindestens 0 und untere 95-%-Grenze nicht unter
   −1,0 Prozentpunkt.
3. **Gewonnene Spiele gegen Solution:** Mittel nicht unter −0,5 Prozentpunkten.
4. **Technik:** kein abgefangener Fehler in irgendeinem Spiel, alle Spiele über 303 Schritte (prüft `par_eval`).

**Bestanden:** Empfehlung an Mahmoud und Moayed, R3 durch das Paket zu ersetzen. Vor einer Abgabe zusätzlich:
Kursrunner auf beiden Seiten und Nachspielen unter Python 3.10 (`scripts/xversion_replay.py`).
**Nicht bestanden:** R3 bleibt die Abgabe. Keine Wiederholung auf anderen Karten und keine nachträgliche Änderung
der Regel.

## Nachtrag 17.11.2026, 09:18, vor dem ersten Bestätigungsspiel: Kandidat

Zweite Prüfung auf 7256200–7256399 (gepaarter Punkteanteil gegen Kaggle): SCHUELER +3,98 [+3,04; +4,96],
SCHUELER_ALLE +3,49 [+2,52; +4,52], HYB_ENS8 +3,87 [+2,93; +4,83]; alle drei bestehen die Regel. Nach der Auswahlregel
tritt **SCHUELER** an (, höchster Wert unter den R3-Varianten).

- Kurspaket , SHA-256
  , gebaut mit  aus der
  eingefrorenen Quelle . Der Bau ist reproduzierbar (gleiche Prüfsumme wie das Probepaket, das in 8 Spielen
  exakt wie  spielte).
- Enthalten: R3 unverändert (v14- und r3-Teil bytegleich), Schüler Ensemble v8 + v8L (SHA-256 ),
  Schüler-Code als , Taktikschicht ohne aktive Taktik.
