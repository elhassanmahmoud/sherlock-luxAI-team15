# Read-only Audit V11–V14 / Remote-Stand 01.11.2026

Stand: HEAD und origin/main `93a2ddd`, Checkout `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`. Geprüft wurden Projektregeln, neuester Arbeitsstand, Releaseberichte/-manifeste, Gate-Log, relevante Quelltexte, vorhandene Gewichte und Ergebnis-CSVs. Keine Spiele, Trainingsjobs, Tests, Builds, Änderungen an Repository-Dateien, Git-Operationen mit Remote oder Push ausgeführt. Einzige Ausgabe ist dieser Bericht.

## Ergebnis und wesentliche Risiken

1. **V14 ist eine ausdrücklich genehmigte Ausnahme, kein bestandener Release-Gate.** Manifest `experiments/releases/20261101_v14_rescue.json` enthält `gate_passed: false`, Mahmouds ausdrückliche Entscheidung vom 01.11., 17:51 („ja lets go“) und die Begründung. Bericht, Arbeitsstand und Plan nennen beide verfehlten Hürden: Mittel-6-Gewinn ≥ +1 pp sowie direkte untere 95%-Grenze > 50 %. Keine versteckte Umdeutung als regulär bestanden gefunden.
2. **Das in den Berichten behauptete fertige `Gruppe15.zip` ist hier nicht vorhanden.** Rekursive Suche unter `/Users/moayedshawesh/Desktop/KI` fand keine `Gruppe*.zip`; Git ignoriert `/Gruppe*.zip`. Daher sind Inhalt, vollständiger Hash, Größe und Zustand des tatsächlich bei Mahmoud liegenden V14-Zips hier nicht unabhängig prüfbar. Versionierte Belege nennen 22.227.522 Bytes, ZIP-Hash nur als Präfix `50c188b1…`, Paketgewicht voll `d3d87209ca3a0a44eae26f052d863e68f54b427cb1b0e19082a21b3bd02e05c4`.
3. **Ein lokaler Neubau würde zwei fremde/unverfolgte Python-Kopien mitnehmen.** `scripts/build_submission.py:sources()` verpackt alle `agents/sherlock/*.py` außer `__init__.py`. Hier liegen zusätzlich `config 2.py` und `reward 2.py`; damit würden 17 statt der dokumentierten 15 Python-Dateien im Paket landen. Dateien wurden weder gelöscht noch geändert. Für einen künftigen Neubau zuerst verfolgte Runtime-Quellen gezielt wählen oder isolierten sauberen Checkout verwenden.
4. **Das vollständige aktuelle 6er-Gegnerpanel ist hier nicht portabel vorhanden.** `experiments/ensembles/league_nets6.pth` und `threat6.pth` fehlen; ebenso die historischen Quellen `battle_v18r.pth`, `battle_v15cx.pth`, `battle_v12.pth` und `battle_mix36c_as.pth`. Aktuelle Abgabe und alle erforderlichen älteren Abgabe-Rollbacks sind dagegen vorhanden. Besonders relevant: `battle_v15.sh` prüft nur Referenz/Kandidat, nicht die HOLD-Dateien. `Agent_x.load_agent()` startet bei einem fehlenden Gewichtspfad lediglich untrainiert. Ohne Vorprüfung könnten vermeintliche HOLD-Duelle daher gegen zufällige Netze laufen. Vor neuen Panel-Jobs fehlende Gegner mit Herkunft/Hash bereitstellen oder einen anderen, vorab dokumentierten Panel wählen.

## Releasebelege und tatsächliche Ergebnisse

Die ausgewählten Bestätigungs-CSVs wurden nur gelesen und ihre Punktwerte nachgezählt. Für V11–V14 und den verworfenen `v19cr` sind Referenz-/Kandidat-Schlüssel `(opponent, seed, side)` jeweils gleich, keine Duplikate vorhanden und jede Gegner/Karte-Kombination hat beide Seiten. Alle verwenden `point_counting_version=2`. Konfidenzintervalle wurden aus dem vorhandenen Gate-Log geprüft, nicht neu berechnet.

| Release | Bestätigung | Nachgezählter Gewinn | Direktduell | Einordnung |
|---|---|---:|---:|---|
| V11 | 806000–806799; direkt 807000–807399 | R 86,5781 → 91,2344 %, +4,65625 pp | 59,5 % [54,5; 64,25] | regulär bestanden |
| V12 | 808000–808799; direkt 808800–809199 | Mittel 6 81,1875 → 87,0833 %, +5,89583 pp | 61,0 % [57,75; 64,38] | regulär bestanden |
| V13 | 300 vorab nach Nebelabzug 25 ausgewählte Karten, 816000–817792 | Mittel 6 84,7778 → 87,1667 %, +2,38889 pp | 56,0 % [50,8; 61,3] | gezieltes Nebel-Gate bestanden |
| V14 | 820000–820799; direkt 821000–821399 | Mittel 6 86,7292 → 87,5938 %, +0,86458 pp | 50,625 % [49,25; 52,0] | ausdrücklich dokumentierte Ausnahme |
| `v19cr` | 822000–822799; direkt 823000–823399 | Mittel 6 −0,35417 pp | 50,625 % [46,5; 54,87] | verworfen, kein Release |

Wichtige Grenzen:

- V11 nutzt ein anderes R-Panel als V12–V14. Die Werte sind keine direkt durchgehende gemeinsame Robustheits-Skala.
- V13s +2,39 pp gelten ausschließlich auf Nebel-25-Karten. Der Gleichheitsblock für andere Karten enthält tatsächlich 720/720 gleiche Ergebnisse (60 Karten × 6 Gegner × 2 Seiten); das beweist keine universelle Gleichheit aller anderen Karten.
- V14 hat im frischen Block bei allen sechs Gegnern positive Punktwerte, gegen Solution_92 94,9375 → 95,4375 % (+8 Ergebnis-Punkte aus 1.600 Spielen). Nicht jeder einzelne Gegnergewinn ist für sich statistisch abgesichert: V3-Intervall schließt 0 ein; V7 und threat6 liegen gerundet bei 0 als Untergrenze. Dev A hat gegen `league_nets6` exakt denselben Wert (73,3333 %), daher ist „in beiden Messungen gegen jeden Gegner besser“ wörtlich zu stark; korrekt ist „beide Panelmittel positiv; frisch alle sechs Gegner im Plus, Dev A keiner schlechter“.
- Die Regel stammt aus älterem Code und die Kartenblöcke sind disjunkt. Das stützt die Replikation. „Unabhängig“ meint hier neue Karten, nicht unabhängige Gegner/Trainingsstarts oder eine Korrektur für die umfangreiche Modellauswahl. Das vorhandene Auswertungsskript weist ausdrücklich auf fehlende Mehrfachvergleichskorrektur hin.
- `v19cr` zeigt den bekannten Auswahl-Effekt: +1,81 pp Dev A, −0,35 pp frisch. Die verfehlte Bestätigung wurde korrekt erhalten und der Kandidat nicht installiert.

## Gewichte, Rückweg und Paketgrenzen

P0 und P1 haben hier beide 24.020.311 Bytes und den vollständigen V14-SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Alle geprüften Rollback-Paare sind bytegleich untereinander und stimmen mit Manifest/Releasebericht überein:

- V13: `experiments/releases/20261101_v13_neb/`, SHA `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`.
- V12: `experiments/releases/20261101_v12_fog/`, SHA `b258dc9927a7094f3d4b83bf4de251b03c3ccc57d69a1da23080c27e806c924b`.
- V11: `experiments/releases/20261031_v11_mix36c_as/` und `20261030_v11_baseline/`, SHA `2ab463e9034357a40cb721b34286ad1f9bad250629bf9f9f17b1d175157cd2e0`.
- V10: `experiments/releases/20261030_v10_V8st/`, SHA `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.

Mit `torch.load(..., weights_only=True)` rein lesend geprüft: V11, V12, V13 und V14 enthalten exakt dieselben 36 Q-Netz-Tensoren. Config-Deltas sind genau V11→V12 (`fog_sap`, `fog_v2`, `splash_min_drop=0.5`, `splash_safe_below=1`), V12→V13 (`est_censor`, `neb_cross`) und V13→V14 (`cand_rescue`, `rescue_after=30`). `cand_post` und `spawn_proof` stehen nicht in der V14-Config und haben im aktuellen Code Standard aus.

Der Checkpoint ist selbstständig: alle Netze sind eingebettet. `ensemble_sources` nennt frühere lokale Quellpfade, `load_agent()` verwendet diese jedoch nicht zum Nachladen. Die fehlende `battle_ft3_18.pth` ist für V14-Inferenz daher kein Hindernis. V3-/V7-Gegner und Solution_92/default sind lokal vorhanden. Das ältere `install_candidates.sh` teilt die Oktober-Kandidaten, nicht die neuen Battle-HOLD-Dateien.

Der Battle-Builder packt nach Quellenprüfung nur Python-Dateien, ein eingefrorenes `agent.pth`, `agents.yaml` und `LIESMICH.txt` unter `Gruppe15/`. Interne Arbeitsstände/Releaseberichte/CSV-Analysen werden nicht kopiert. Für einen sauberen Build ist daher die oben genannte lokale Python-Glob-Verunreinigung der konkrete Befund. Abgabegewicht im Repo hat absichtlich noch kein `frozen`; der Builder ergänzt `frozen=True`. Daher sind unterschiedliche Datei-Hashes zwischen Repo und Zip erwartbar, Tensor-/Config-Abgleich ist nötig.

Vorhandene Runner-Berichte V11–V14 melden `passed`; V14 dokumentiert 8 Spiele, frisches Gedächtnis, verifizierte geladene Modelle, maximal 11,623 ms/act. Die dokumentierten 632 Tests sowie Python-3.10-Replayprüfungen sind historische Aussagen von Mahmouds Umgebung; hier nicht neu ausgeführt. Die drei Replay-Spiele ersetzen keine umfassende Versions- oder Leistungsbestätigung. Kurs-Zeitlimit bleibt laut Runner-Bericht unbekannt.

## Koordination / Remote-Watch

Neuester Arbeitsstand 01.11., 18:48: Folien fertig, Moayed soll Folien prüfen, beide sollen proben; Mahmoud lädt das V14-Zip bis Mittwochnacht hoch. Jüngste protokollierte Messung `v19cr` endete 17:28. Runde 7 (`pipeline_battle_ft7.sh`) ist ausdrücklich „nicht gestartet, nicht versioniert“ und zurückgestellt. Im vorliegenden Remote-Stand gibt es keine spätere Ankündigung eines konkreten laufenden/neuen Trainings- oder Evaluationsjobs. Der allgemeine Verbesserungsauftrag bleibt bestehen; daraus folgt keine Aussage über unveröffentlichte Arbeit auf Mahmouds Rechner.

Die Blöcke 820000–821399 und 822000–823399 gelten nach den vorhandenen Messungen als verbraucht. Die frühere V13-Notiz, sie seien unbenutzt, ist historisch und wird vom jüngeren V14-Eintrag abgelöst. Vor neuen Arbeiten Remote-SHA/Arbeitsstand erneut abgleichen. Kein eigener Pollingloop gestartet; neue vom Root gemeldete SHAs können gezielt read-only nachgeprüft werden.
