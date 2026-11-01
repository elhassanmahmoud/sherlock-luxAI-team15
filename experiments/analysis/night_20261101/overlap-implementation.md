# Opt-in Überlappungsinferenz – Umsetzung und Belege

Arbeitskopie ausschließlich `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`, Branch `improvement/november-battle-20261101`, Start `93a2ddd`. Umsetzung nach Rootfreigabe/Design; keine Commits durch diesen Agenten.

## Geänderte Dateien

- `agents/sherlock/belief.py`: neuer Konstruktorparameter `overlap_infer=False`; begrenzter Helper `_overlap_differences`; Aufruf bei gültigen neuen eigenen und gegnerischen Punktegleichungen. Im eigenen Spawnfenster wird der Helper auch bei bestehenden Window-Schaltern nicht aktiviert. Der gegnerische Pfad hat bereits `_stable` als Vorbedingung.
- `agents/sherlock/config.py`: neuer Bool mit Default false; alte Checkpoints erhalten den ausgeschalteten Default über das bestehende `from_dict`.
- `agents/sherlock/main.py`: ausschließlich Übergabe des Config-Bools an den Belief.
- `tests/test_overlap_inference.py`: 24 gezielte Tests, einschließlich unabhängiger erschöpfender Wahrheitsprüfung.

Keine Gewichte, Training, Modellspiele, Seedreservierungen, Projekt-Dokumentation oder fremde Dateien verändert. Andere unversionierte Nachtdateien gehören Root/anderen Agenten und wurden erhalten. Root koordiniert Vollsuite, Spielkompatibilität und spätere Experimente.

## Mathematische Garantie

Nach Abzug bewiesener positiver/Nullfelder: `sum(A)=a`, `sum(B)=b`, binäre Feldwerte. Setze `I=A∩B`, `L=A\B`, `R=B\A`. Für `z=sum(I)` gilt exakt:

```text
lo = max(0, a-|L|, b-|R|)
hi = min(|I|, a, b)
lo <= z <= hi
sum(L)-sum(R) = a-b
```

Bei `lo>hi` oder einzeln unzulässigen Restwerten liefert der Helper **keine** neuen Fakten. Andernfalls erzwingt `a-b=|L|` alle L positiv und alle R null. Der inverse Extremfall `a-b=-|R|` erzwingt alle L null und alle R positiv. Es werden nur teilweise überlappende Mengen mit nichtleeren L/I/R erweitert. Die bestehende Teilmengenlogik und ihr Schalter bleiben erhalten.

Schlüsse werden über alle verglichenen Records in zwei Sets gesammelt. Ein Feld darf weder direkt noch über bestehende Spiegelsymmetrie zugleich positiv und null werden; widersprüchliche Batches liefern keine neuen Fakten. Die vorhandene Propagation validiert selbst nicht jede Inkonsistenz, deshalb erfolgt diese Prüfung davor. Match-/Spawnregeln, Reset und `_mark_*`-Symmetrie sind unverändert.

## Begrenzung

Der Helper vergleicht nur die eine neue Gleichung mit `records[:MAX_RECORDS]`, also höchstens 400 vorhandenen Records. Rohmengen über 16 Felder werden vor jeder Expansion übersprungen. Begründung: reguläre eigene/gegnerische Beobachtungen enthalten maximal 16 einzigartige besetzte Felder; größere aggregierte Schlussmengen werden bewusst nicht wieder als Overlap-Eingabe verwendet. Das verliert höchstens weitere Schlüsse, macht keine unsicheren Schlüsse.

Damit höchstens 400×16 Feldvergleiche zuzüglich Setoperationen/Konstanten und Sortierung von höchstens 576 Schlussfeldern auf der 24×24-Karte. Nur zwei aggregierte zusätzliche Extremgleichungen, keine neue rekursive Abschlusssuche und keine neue All-Pairs-Schleife. Der bestehende 400er-Record-Cap und die bisherige `_propagate`-Fixpunktiteration bleiben aktiv.

## RED: vor Produktivänderung ausgeführt

Interpreter `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`, cwd Arbeitskopie. Nach Root-Baseline, mit Trainingsagent abgestimmtes exklusives Testfenster:

```text
python -m pytest -q tests/test_overlap_inference.py \
  -k 'partial_overlap_proves_both_exclusive_tiles or config_roundtrip_and_agent_wiring'
3 failed, 20 deselected in 2.65s
```

Zwei erwartete Assertion-Fehler: `{100,101,102}=2`, `{101,102,103}=1` beweisen im alten Code 100 nicht, in beiden Beobachtungsreihenfolgen. Dritter erwarteter Assertion-Fehler: `AgentConfig.from_dict` übernimmt den noch fehlenden Schalter nicht. Vollständiges Log `/tmp/sherlock-night-20261101/overlap-red.log`. Keine Import-/Setupfehler.

## GREEN und fokussierte Regression

Erster Lauf nach Umsetzung:

```text
python -m pytest -q tests/test_overlap_inference.py
23 passed in 3.27s
```

Danach zusätzliche integrierte 400er-Cap-Prüfung ergänzt. Abschließender gezielter Lauf:

```text
python -m pytest -q tests/test_overlap_inference.py tests/test_belief.py \
  tests/test_rules_1910.py tests/test_relic_prior.py tests/test_opp_point_infer.py
78 passed in 3.38s
```

Logs `/tmp/sherlock-night-20261101/overlap-green.log` und `overlap-focused.log`. `git diff --check` ohne Befund. Keine Vollsuite durch diesen Agenten: Root hat sie ausdrücklich zentral koordiniert und parallele Torchjobs untersagt; dessen vorgelagerte Baseline ist keine Nachher-Verifikation dieses Changes.

## Inhalt der gezielten Prüfungen

- Beide Extremfälle durch umgekehrte Beobachtungsreihenfolge; neue Inferenz funktioniert unabhängig vom Subset-Schalter.
- Nicht extreme Gleichungen bleiben unentschieden; Default aus erhält bisherige Record-/Faktsequenzen auf 30 festen synthetischen Beobachtungen.
- Constructor, Config-Roundtrip, alte leere Config, echtes Agent-Wiring ohne Modellevaluation.
- Spawnfenster, Matchreset und bereits vorhandene Spiegelsymmetrie; Normalisierung schon bewiesener Fakten.
- Ungültige Restwerte, leere Mengen, widersprüchliche gemeinsame Summen, direkt und symmetrisch widersprüchliche Schlussbatches.
- Alle **2304** Kombinationen zweier Teilmengen eines Vier-Feld-Universums und zulässiger Restsummen, jeweils unabhängig gegen alle 16 binären Feldbelegungen geprüft. Jede abgeleitete Aussage gilt für jede mögliche Belegung; bei unmöglichem Paar keine neue Aussage. Alle Orientierungen, verschachtelte/disjunkte/gleiche Mengen sind enthalten.
- Größenlimit vor Expansion geprüft; 401. Record wird nicht betrachtet.
- Dichter Grenzfall: 400 Records zu je 16 Feldern, 50 Helper-Aufrufe unter der großzügigen 5-Sekunden-Prüfgrenze, höchstens zwei aggregierte Ergebnisse, Ausgangsrecords unverändert. Integrierter Inferenzpfad behält danach `len(records)<=400`.

## Offen für Rootreview

Keine Aussage über Spielstärke oder Häufigkeit zusätzlicher Schlüsse. Es fehlen weiterhin der vorgesehene Diagnosetrace, reale Flag-aus-Aktionskompatibilität und unabhängiges Review. Kandidat erst bei zusätzlicher nachweislicher Informationswirkung zulassen; `cand_post`/`spawn_proof` bleiben unverändert aus.
