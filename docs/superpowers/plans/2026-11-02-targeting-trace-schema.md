# Passiver Ziel-/Aktions-Trace: verbindlicher erster Auftrag

Gilt vor jeder neuen Policywahl. Ergänzt den Fortsetzungsplan vom 02.11.;
keine Freigabe für eine produktive Agentenänderung oder Leistungsstudie.

## Schnittstelle und Ablage

- `scripts/targeting_probe.py`, `tests/test_targeting_probe.py`; keine Änderungen
  an `agents/`, `lux/runner.py`, Gewichten oder historischen Messdaten.
- Öffentliche reine Hilfsfunktion
  `classify_frame(ctx, masks, q_values, final_actions, truth=None) -> dict`:
  Kontext und Aktionen bereits kanonisch, Q-Matrix in `ctx['ally_ids']`-Reihenfolge;
  Rückgabe vollständig JSON-kompatibel, keine Eingaben ändern. `truth=None`
  erlaubt dieselbe agentensichtige Messung ohne Wahrheitsdaten.
  `masks` ist dict[int, bool[6]], `q_values` float32[len(ally_ids),6],
  `final_actions` int[max_units,3] im kanonischen Raum. Optionale `truth` enthält
  `point_tiles` bool[W,H], `enemy_positions` int[N,2], `enemy_energy` float[N]
  ebenfalls kanonisch; unmaskierte ungültige Positionen vorher entfernen.
- `DecisionObserver(agent)` als Kontextmanager: kopierende Forward-Hooks auf
  `q` und `extra_q`; Originalmethoden genau einmal aufrufen, beim Verlassen auch
  nach Fehlern alle Hooks/Wrapper entfernen. Kein neues `act`, `observe`,
  Netzforward, RNG oder `_enemy_stationary`-Aufruf. Vorhandene Ausgabe kopieren,
  bevor die In-place-Maske greift. Gleiche Torch-Reihenfolge/float32-Mittelung.
  Der Observer umhüllt den vorhandenen `agent.act`-Aufruf und stellt danach
  `last_frame` bereit. Er ist für train=False, sechs Aktionen und ohne
  `cnn_policy` bestimmt; andere Politikpfade vor Installation der Hooks ablehnen,
  statt nicht tatsächlich verwendete Q-Werte auszugeben.
- CLI `python -m scripts.targeting_probe --weights PATH --keys JSON --out DIR`;
  neue Ausgabe, bestehende Ausgabe und fehlende Gewichte vor einem Spiel ablehnen.
  Keys im Format `/tmp/sherlock-continue-20261102/diagnostic_keys.json`:
  `keys`-Liste von seed/side/group, nur `solution92` in diesem Auftrag.
- Je Schlüssel ein unbeobachtetes und ein beobachtetes vollständiges Spiel,
  nacheinander, ein Worker. Vergleich nativer Aktionsbytes mit Shape/Dtype-Header,
  aller Spiel-/Matchsiege, Punktzählung v2 und Schrittzahl. Die bekannte Quelle
  `selection_baseline.csv` zusätzlich gegen Ergebnis/Wins/Punktetotale prüfen.
  Neue Daten in `experiments/analysis/continuation_20261102/targeting/`.
  Pro Spiel komprimierter JSONL-Trace plus Gesamtmanifest/Passivitätsbeleg;
  niemals alte Ausgaben ersetzen. Script selbst darf noch keinen langen Job starten.

## Pro Schritt

Key `(seed,side,match_idx,obs_step,match_step)`. Native Reset-Schritte mitzählen,
aber als Reset markieren, keine alten Cache-Kontexte als aktuelle Entscheidung.
Bei fehlendem/passend fehlendem Cache expliziter Status statt erfundener Q-Daten.
Nach normalem `act` genau den passenden Cache lesen.

1. Kopierte öffentliche Ebene: IDs/Positionen/Energie, sichtbare Gegner,
   Punkt-/Kandidaten-/Passierbarkeits-/Nebel-/Energiekarte, zugewiesene Ziele,
   `first_on_tile`, Kosten, Sensor und aktive relevante Schalter. Energiefrische
   separat aus **realer** Sensorsicht verfolgen; `belief.last_seen` enthält auch
   Symmetriesicht und darf nicht als Energiealter ausgegeben werden.
2. Je Unit: 79 tatsächliche Merkmale, kopiertes gemitteltes Q[6], Maske,
   raw/masked argmax und finale native/kanonische Aktion; Klasse negative Energie,
   unter Bewegungskosten, unter Sapkosten oder genügend Sapenergie. Holder nur
   erste/niedrigste ID unter eigenen Units mit nichtnegativer Energie auf einem
   bekannten Punktefeld. `ctx.first_on_tile` als Legacy-Planwert separat erhalten:
   bei negativer Legacy-Unit bleibt die einzige lebende Unit ein produktiver Halter,
   keine frei verfügbare gestapelte Reserve. Gestapelte lebende Units getrennt.
   BFS-Distanz zum Istziel und erlaubte erste
   BFS-verkürzende Richtungen; Manhattan nicht als BFS etikettieren.
3. Maskengründe nur soweit aus öffentlichen Daten exakt ableitbar:
   Energie/Rand/nach Gedächtnis unpassierbar und sichtbare Besetzung. Für weitere
   Sperren `later_guard_unresolved`; keine Simulation der Maskenentscheidung
   als unabhängigen Beleg ausgeben. Vorhandene Maske bleibt maßgeblich.
4. Wrapper-Ereignisse für `_rule_override`, `_path_fix`, `_obey_target`,
   `_soft_nebula`, `_no_strand`, `_fog_sap`, `_artillery_ok`, `_overkill`:
   Unit, Reihenfolge, kopierte Eingabe/Rückgabe und relevante mutable Argumente
   (insbesondere planned_dmg). Nicht instrumentierte Inline-Übergänge als
   unaufgelöst kennzeichnen; beobachtetes Artillerie-OK alleine beweist keine
   vollständig rekonstruierte frühere Bewegungsaktion.
   Optional darf der Wrapper die aktuelle lokale Aktion `a` aus seinem direkten
   `_act`-Aufrufer rein lesend kopieren, nur bei gleicher Unit-ID und passendem
   Funktionsnamen. Sonst `caller_action=null`; Frame nicht dauerhaft halten.
   Das macht eine echte Vor-Artillerie-Aktion beobachtbar, ohne sie aus Q-Werten
   zu erraten oder Produktionscode umzuschreiben.

## Freie eigene Felder und Gegenfaktum

Eigene Hälfte x+y<=W−1 im kanonischen Raum wie bisherige Mechanismusmetrik.
Je bekanntem Feld ohne eigene maskierte Unit: sichtbarer Gegner, zugewiesene
Unit(s), nach Gedächtnis passierbar, min. BFS lebender Units und beweglicher
Nicht-Halter, vorhandener erlaubter erster Fortschritt. Negative Energie,
Energie unter move_cost, sole holder und Stacker nicht vermischen. Dauer jeder
Freiphase nach Matchreset neu beginnen. Mehrere Hindernisse dürfen zusammen
auftreten; keine exklusive Schuldklasse erzwingen. Keine volle Wegenergie oder
sichere Ankunft aus einem erlaubten ersten Schritt ableiten.

Nur diagnostisches Zwei-Eigentümer-Gegenfaktum: höchstens 120 Unitpaare je Step,
beide bewegliche Nicht-Halter, zwei bereits zugewiesene **eigene bekannte**
Punkteziele. Beide alten/neuen BFS-Wege erreichbar und für beide Alternativen
erlaubter erster Fortschritt. Gleiches Zielset, nur strikt kleinere BFS-Summe
notieren; keine Zielzuweisung verändern und keine globale Optimalität behaupten.
Bei V14 sind Heim-/Energie-/Stickyboni aus, bei anderer unpassender Config diese
Berechnung als nicht zugelassen markieren statt einen falschen Kostenvorteil.

## Nachgelagerte Wahrheit

Erst nach der Aktionswahl in einem separaten Objekt: wahre Punkte, gegnerische
Belegung einschließlich Unsichtbarer, wahrer Asteroid, echte Position/Energie
vor und nach env.step. Bereits vorhandene `mechanism_probe`-Ereignissimulation
kann Energiephasen ergänzen, muss ausdrücklich als Rekonstruktion bezeichnet
werden. Reset/Tod/Nummernwiederverwendung nicht zu echter Bewegung vermischen.
lowE aus der alten Mechanismusmessung ist nach Bewegungskosten, **vor** Sap/
Void/Feld, kein unmittelbarer Beweis einer Sapverschwendung. Keine Wahrheit an
Agent oder Kontext zurückschreiben.

## Prüfungen vor Interpretation

Rote Verhaltenstests zuerst: erlaubter/unerreichbarer Weg, verborgener Gegner
nur in posthoc, negative Energie vs Halter/Stacker, rohe vs maskierte vs finale
Aktion, Eingabe-Unveränderlichkeit, Spieler-1-Kanonisierung, Reset/Cache-Mismatch,
Q-Hook vor Maskierung und Entfernung aller Wrapper/Hooks nach Fehlern.
Gegenbeispiel für 2-Tausch: Units (0,0),(3,0), gewählte Ziele (4,0),(2,0):
BFS-Summe 5 statt 3; ein sole holder, unerreichbarer oder maskierter Fortschritt
darf den Versuch nicht als zugelassene Versorgung ausgeben.

Mindestens alle 12 festgelegten Schlüssel traced/untraced exakt passiv (24
Spiele), 303 Schritte pro vollständigem Spiel. Vollsuite nach neuem Werkzeug
ohne gleichzeitigen Modelljob; unabhängiger Code-/Datenreview. Fehlende Felder
oder unvollständige Rekonstruktion offen benennen, nicht still aus Annahmen füllen.
