# Unabhängige V4-Bestätigung – 21.10.2026

**Vollständig: 2.400 Spiele. Auswahlentscheidung: `no_promotion_gate_failed`.**

Vorab festgelegt in [Plan](../../../../docs/superpowers/plans/2026-10-21-v4-independent-confirmation.md), Commit `d51a790`; Quellenstand `6ab3109`. V3 und V4 unverändert geladen, keine Config-Overrides, kein Training. V4 enthält dieselben 18 Netztensoren wie V3, zusätzlich die gespeicherten Inferenzschalter `contest_sap` und `opp_infer`.

| Vergleich | Karten / Spiele | V3 Siege/Remis/Niederlagen | V4 Siege/Remis/Niederlagen | Unterschied / Intervall |
|---|---|---|---|---|
| default | 510800–510999, je 400 | 400/0/0 | 400/0/0 | V4−V3 0,000 pp; 95%-Karten-KI [0,000; 0,000] pp |
| solution92 | 510800–510999, je 400 | 311/0/89 | 313/0/87 | V4−V3 0,500 pp; 95%-Karten-KI [-3,000; 4,000] pp |
| Direkt V4 gegen V3 | 510400–510799, 800 | — | 408/0/392 | V4-Score 51,000 %; 95%-Karten-KI [48,125; 54,000] % |

## Entscheidung nach den vorher festgelegten Regeln

- `solution92_delta_positive`: True.
- `solution92_lower95_positive`: False.
- `default_loss_at_most_2pp`: True.
- Untere Direktvergleichsgrenze strikt über 50 %: False.

Alle Bedingungen müssen zugleich erfüllt sein. Ein statistisch qualifizierter Kandidat benötigt anschließend technische Kursprüfung, Reproduktion und eine versionierte V3-Sicherung. Die beiden Vorteils-Gates sind verfehlt; daher bleibt V3 unverändert installiert. Dieses Experiment selbst installiert keine Gewichte. Aktueller Abgabestand und Folgearbeit stehen im [Arbeitsstand](../../../../docs/ARBEITSSTAND.md).

## Prüfung und Grenzen

Laufzeit UTC: 2026-10-21T05:35:38+00:00 bis 2026-10-21T06:04:21+00:00. Zwei Worker insgesamt. Alle drei Jobs vollständig und vor der Frist 08:40 Berlin beendet. Keine Ergebnisabhängigkeit der Laufreihenfolge oder Stichprobengröße; alte V4-Versuche nicht gepoolt.

Unabhängiger Root-Audit und zweiter Review prüfen exakte 800 Schlüssel pro CSV, beide Seiten, alle drei Matches (303 Schritte), Punktezählversion 2, endliche Messwerte, konsistente Spiel-/Punkteresultate, Ausführungskommandos, alle Quell-/Input-/Interpreterhashes und den unveränderten HEAD. Kartenbootstrap unabhängig erneut berechnet: 5.000 Ziehungen, Seed 0, ganze Kartenpaare; Kandidaten bei Gegnervergleich gepaart. Rohdaten und Audits in diesem Ordner, Bytehashes in `archive_manifest.json`. Die vorherige vollständige Testsuite bestand mit 223 Tests und 14 Subtests; Log enthalten.

Die Intervalle gelten für diese festen Agenten und Kartenstichproben. Default-Toleranz ist eine beobachtete Grenze, kein Nichtunterlegenheitsnachweis. Wiederholte Untersuchung der V4-Hypothese begrenzt nominelle Signifikanz; kein Karten-Nachlegen und keine Behauptung allgemeiner Turnierüberlegenheit. Ein verfehltes Gate beweist keine Gleichwertigkeit oder Wirkungslosigkeit. Das Default-Intervall [0; 0] entsteht aus identischen Erfolgen auf allen getesteten Karten; es garantiert keine fehlerfreie Leistung auf anderen Karten.

## Reproduktion

Die CSVs konservieren ihre ursprünglichen Bytes (`../.gitattributes`). `state.json` enthält die exakten absoluten historischen Kommandos, Konfigurationen und Identitäten. Für einen erneuten Lauf vom Repo aus relative Gewichtswege und **neue, noch nicht vorhandene** Ausgabepfade verwenden; die Karten sind ab jetzt bekannte Reproduktionskarten, keine frischen Tests. Numerische Threads auf eins, höchstens zwei Worker insgesamt.

```sh
python -B -m scripts.par_eval --weights experiments/candidates/all18_v4.pth --first 10400 --n 400 --workers 2 --opponents self:experiments/candidates/all18_v3.pth --out /NEUER/PFAD/direct.csv
python -B -m scripts.par_eval --weights experiments/candidates/all18_v3.pth --first 10800 --n 200 --workers 2 --opponents default,solution92 --out /NEUER/PFAD/v3.csv
python -B -m scripts.par_eval --weights experiments/candidates/all18_v4.pth --first 10800 --n 200 --workers 2 --opponents default,solution92 --out /NEUER/PFAD/v4.csv
```

Die Dateien unter `historical_tools/` sind bytegleiche Textsnapshots des damaligen Ablaufs und der Tests. Sie enthalten feste /tmp-Abhängigkeiten, Maschinenpfade, Quellhashes und eine abgelaufene Frist. Nicht unverändert als neue allgemeine Pipeline starten. Der unabhängige Audit bindet absichtlich den damaligen HEAD; nach dem Archivcommit erfolgt die Archivprüfung anhand der gespeicherten Hashes.
