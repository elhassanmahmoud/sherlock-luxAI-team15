# Unabhängiger statischer Prototyp-/Testreview

09.11.2026. **PASS im geprüften technischen Umfang; keine konkreten Blocker gefunden.** Vollständige Implementierung, vollständige Testdatei, `IMPLEMENTATION.md` sowie RED-/FIRST_FULL-/GREEN-Rohlogs gelesen und gegen Plan und ursprüngliche Buchhaltung geprüft. Keine neue Ausführung durch den Reviewer.

## Gebundene Fassung

| Datei | SHA256 |
|---|---|
| `scripts/sap_leading_agent.py` | `3b4b779f25f32af9f523b69b169a68eea78b862ce89ede77a3138ef2db26c2eb` |
| `tests/test_sap_leading_agent.py` | `1e3c5835af3bc8f823a7383de2bcec5a11bf188377f699a3a5b3d03b6b50ea22` |
| `IMPLEMENTATION.md` | `3fa489f7dbab463cc30cd14a830266a1c0807131b967777670dfe94003d8ece5` |
| `GREEN.log` | `98785bd0cb049358efc5dd3df77560b7b63bb629b1e53d1f3781985abe84a3ad` |
| `RED.log` | `095341aec48bca1fc1083f478ff3b3de9afd79da93d9cf1f46f89485defd4292` |
| Technischer Plan `docs/superpowers/plans/2026-11-08-sap-leading-prototype.md` | `89d0e81f895d85c375e33e45726741348f7af78aadd6b898a1153cc1467c706f` |
| Vorheriger `/tmp/sap-leading-bookkeeping-review.md` | `3477493b4082f5cf8c45106c03adbf1373d712264c4dd2c6c5e68050873b42a9` |

Originalquellen erneut abgeglichen: `agents/sherlock/main.py` SHA `108ea9cb072bbdba0987d91873a7001cedda420b965da96cd9e9090e7c1d33bc`, `param_est.py` SHA `c98eae7b8afba125bc7df3b2e8371b3c00a89ead149d3058a1dbc448affd8419`. Zusätzlich Kontextbildung, Spiegelungsfunktionen und Eval-Spielaufruf lesend geprüft.

## Prüfergebnis

- **Realer Aufrufvertrag:** Die Unterklasse überschreibt `_act`, nicht `_act_est`. Genau ein `super()._act` wird ausgeführt. Der unveränderte Corepfad beobachtet vorher und erinnert danach; weder zusätzliche Modellentscheidung noch zusätzlicher Observe-/Remember-Aufruf. Die explizite Verweigerung einer Intervention bei deaktiviertem ursprünglichem Estimatorpfad entspricht dessen tatsächlichen Evalbedingungen. Der synthetische Integrationstest verwendet das originale `_act_est` und originale `remember`; nur `observe` liefert kontrolliert den neuen Posterior.
- **Auswahl und Begrenzung:** Nur bereits finale SAP-Zeilen; eigene Energie, altes Zentrum, eindeutige öffentliche Ziel-UID, unmittelbare Schritt-/Matchfolge, kardinale Bewegung, beide Gegnerenergien, aktuelle Bewegungskosten, neues sichtbares/passierbares legales Zentrum und Parameterschwelle werden geprüft. Keine Zukunfts-/Enginewahrheit. Die aufsteigend sortierte Liste aller finalen SAP-UIDs führt zum kleinsten tatsächlich geeigneten Schützen; höchstens dessen Offset wird geändert. Alle anderen Befehle bleiben erhalten.
- **Reset und Historie:** Der originale Episodenreset bleibt erhalten; eigener Verlauf und Messzähler werden dort zurückgesetzt. Matchstep0, fehlender/veralteter Cache und nicht identischer aktueller Kontext unterbrechen den Verlauf. Schritt, Matchstep, Matchindex und Spiegelungsmodus müssen anschließen. Gespeicherte Positionen/Energien sind kopierte Tupel/Skalare, keine Ansichten mutierbarer Beobachtungsarrays. Der bereits aktualisierte `_enemy_prev` wird nicht für die alte Position verwendet oder zurückgesetzt.
- **Deaktivierter Modus:** Standardmäßig `lead_enabled=False`; nach genau einem Coreaufruf unveränderte Ausgabe, keine Kandidaten-/Posteriorprüfung und kein eigener Verlauf. Produktive Aktions-, Treffer-, Pending- und Messdaten des Core bleiben erhalten. Die ausdrücklich verlangten Eval-Sperren `learn_enabled=False` und `autosave_on_terminate=False` gelten auch hier; sie sind keine Behauptung vollständiger Attributgleichheit zu einem unbeschränkten Basiskonstruktor.
- **Buchhaltung:** Neuer `_sap_hits`-Wert zählt aktuelle sichtbare Gegner im neuen3×3-Bereich. `sap_hits_est` erhält nur die Booldifferenz gegenüber dem gespeicherten alten Wert, `sap_attempts` keinen zweiten Zuwachs. Nur der gewählte UID wird aus `_sap_unknown` entfernt. `_prev_actions`, Features, Masken, Cache und beide Pendinglisten werden nicht umgeschrieben; SAP-Klasse, Eigenposition und Kosten bleiben gleich. Keine Nachplanung weiterer Units.
- **Spiegelung:** Ausschließlich `belief.mirrored` bestimmt `(-dy,-dx)` für die Rückführung des alten nativen Offsets und Ausgabe des neuen. Sensorbeobachtung wird einmal in denselben Raum gebracht; Kontextpositionen bleiben bereits kanonisch. `[x,y]` und Chebyshev-Reichweite stimmen mit dem Core überein.
- **Messzähler:** Eigene Zähler beeinflussen keine Auswahl. Finale SAPs werden über Ausschlüsse, geeignete zusätzliche Schützen oder eine Änderung erfasst; pro Spiel kumulativ, letzter Änderungsbeleg separat. Keine behaupteten tatsächlichen Treffer durch prognostizierte Folgepositionen.

## Vorhandene Tests und Aussagegrenzen

Der gelesene finale Rohlog enthält **44 passed in1.55s**. RED belegt zwei ursprünglich unveränderte Offsets; der Zwischenlauf und seine dokumentierte log/exp-Grenzfallkorrektur passen zu den finalen Tests. Die echte Schätzermethode behält die Schwelle0,9; separate synthetische Posteriorfälle prüfen0,9 und den direkten kleineren Gleitkommawert. Weitere Fälle decken beide Spiegelungen, Achsen, Energie-/Reichweitengrenzen, fehlende Historie, Reset, Cache, kleinsten geeigneten UID, Statistikdelta und ursprüngliches Remember ab.

Dies sind **isolierte synthetische Hooktests**: Basiskonstruktor und Core-`_act` sind ersetzt; `QNet`-Konstruktion und `torch.load` werden gesperrt. Sie beweisen keine tatsächliche36-Netz-/Checkpoint-/Spielintegration. Der statische Abgleich bestätigt den realen Einhängepunkt, ersetzt aber keinen später gesondert festgelegten Laufnachweis. Die Originalparameterbeobachtung ist im Integrationstest kontrolliert ersetzt; ihre allgemeine Schätzgüte wird hier nicht neu bewertet.

Keine Tests, Imports, Modelle, Spiele oder Repositoryänderungen durch diesen Reviewer; nur diese externe Reviewdatei geschrieben. Der Review ist **keine Aufnahme-, Spielstart-, Regelübernahme- oder Stärkefreigabe**. Ein späterer Vergleich benötigt weiterhin den eigenen festen Plan und Root-Abnahme; Identitäts-/Sichtbarkeitsheuristik, Parameterunsicherheit sowie die unter altem Ziel bereits abgeschlossene Teamplanung bleiben fachliche Wirkungsgrenzen.
