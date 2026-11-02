# Zwei begrenzte Sherlock-Prototypen

## Evidenz und Ziel

Der unabhängig geprüfte passive Trace (`continuation_20261102/targeting_audit.md`)
zeigt H1:16 Artillerie-Stornierungsketten, davon3 verhinderte erste Fortschritte
zu eigenen bekannten Punkten; H2:141 feste-Zielset-Tauschgelegenheiten in91 Frames.
Beide Kohorten betroffen, keine repräsentativen Prävalenzen und kein Sieggewinn.
Ziel ist ein kleiner überprüfbarer Eingriff, kein neuer Heimbonus/Energiereward.
Alle bisherigen V14-Tensoren und Sicherungen bleiben unverändert.

## H1: unnötige Artillerie früh abweisen

Neuer Configschalter `art_move_guard: bool = False`. Nur wenn die bestehende
Artillerieregel gerade eine erlaubte Bewegungsaktion1–4 durch SAP ersetzen würde,
`sap_no_overkill` samt dessen Trainingsfreigabe aktiv ist und die bestehende reine
`_overkill(ctx,uid,sap,planned_dmg)`-Prüfung bereits wahr liefert: Artillerie-SAP
nicht erzwingen. Aktuelle Bewegung bleibt für die **normale nachfolgende**
Nebel-/Strand-/Gefahrenkette erhalten. Keine späte Wiederherstellung duplizieren.

`_overkill` wurde quellengeprüft: liest Kontext/Plan, keine Zustandsänderung.
Ursprünglich vom Netz gewählte SAPs, ursprüngliches STAY, lebende Ziele,
deaktivierter Overkillschutz und ausgeschalteter Schalter verhalten sich wie
bisher. Keine neue Sapzielwahl und kein globales Next-best-action-Verfahren.
Optionaler Zähler `art_move_kept` bezeichnet die erhaltene Vor-Artillerie-Aktion,
keine garantierte ausgeführte Bewegung oder gewonnenen Punkte.

## H2: genau einen besseren Eigentümertausch

Neuer Schalter `point_pair_swap: bool = False`, reine Funktion
`improve_point_assignment(ctx, masks, cfg) -> (assigned: dict, bfs_gain: int)`
in `agents/sherlock/assignment.py`.

- Ausgabe kopiert die bestehende Zuweisung, verändert weder Eingaben noch das
  ausgewählte Zielset. Pro Step höchstens **ein** Tausch, keine Konvergenzschleife.
- Zulassung wie im Trace konservativ: `use_belief` und `reach_assign` wahr,
  `home_first`, `home_penalty`, `energy_pref`, `sticky` aus/0. Sonst unverändert/0.
- Nur bewegliche Nicht-Halter (Energie≥move_cost). Produktiver Halter ist die
  niedrigste lebende ID auf einem bekannten Punkt, unabhängig vom Legacywert
  `first_on_tile`; lebende Stacker dürfen grundsätzlich teilnehmen.
- Beide bereits gewählten unterschiedlichen Ziele sind bekannte eigene Punkte.
  Eigene Hälfte aus Belief-Kanonisierung/Team ableiten; keine Gegnerziele,
  Kandidaten oder Erkundungsziele hinzufügen/entfernen.
- Beide Ursprünge/Ziele nach Gedächtnis passierbar, alle vier BFS-Wege erreichbar
  und je Alternative ein nach tatsächlicher Maske erlaubter erster Fortschritt.
  Aktuell zulässiger erster Schritt ist keine sichere gesamte Route.
- Unter höchstens120 Paaren das mit maximaler **strikter** BFS-Summenverbesserung
  wählen; Gleichstand nach aufsteigenden Unit-IDs. Kein Tausch bei Gleichstand0,
  negativen Energien, Halter, blockiertem Pfad oder verbotenen ersten Schritten.
- Bestehendes `features.bfs_maps` darf auf den wenigen zulässigen Zielkoordinaten
  genutzt werden. Bei weniger als zwei geeigneten Units kein BFS. Keine neue
  Bibliothek, keine Wahrheit, kein RNG oder zusätzlicher Netzforward.

Einbindung `_decide`: nur im aktivierten/freigegebenen Pfad aktuelle Sapziele und
Masken wie bisher berechnen, Tausch **vor** `build_features`/Q durchführen und
dann dieselben Masken verwenden (deren Bewegungsteil hängt nicht vom Ziel ab).
Ausgeschalteter Pfad behält seine bestehende Reihenfolge. `feat_belief` muss der
vollständige Agentenbelief sein; bei inkompatibler Memoryless-Ablation nicht
verdeckt abweichende Ziele an die Features geben. Im Training nur mit bereits
vorhandenem `rules_in_training` anwenden. Cache verhindert Mehrfachzählung.
`point_pair_swaps`/`point_pair_bfs_gain` zählen lokale Planänderung/Potential,
keine realisierten Wege oder Punkte. Bestehende Masken/Bewegungsregeln bleiben.

## Technische Abnahme vor Leistungskandidaten

TDD: greedy-Gegenbeispiel Units(0,0)/(3,0), Ziele(4,0)/(2,0) wird5→3; maximal
ein bester Tausch, deterministische Ties, unverändertes Zielset/Eingaben,
Halter/negative/Stacker/Masken/unpassierbar/unerreichbar, beide Teamorientierungen,
inkompatible Config, Features nach Tausch und Default-off-Pfad. H1 testet echte
Routingkette, lebendes/totes Ziel, Original-SAP/STAY, disabled und Trainingsgate;
erhaltener Zug muss weiter durch vorhandene Nebelprüfung gehen.

Nach Code-/Testreview frische technische Läufe auf **verbrauchten** Schlüsseln:
neuer Default-off-Agent auf allen12 vorhandenen Schlüsseln gegen die exakt
protokollierten alten nativen Streamhashes; weitere aktivierte Smoke-Läufe vorab
festlegen. Diese Spiele sind keine Stärkenauswahl. V14-Gewichte read-only.

## Nachfolgende Kandidatenwahl, noch keine Leistungsfreigabe

Die Prototypen können einzeln und zusammen technisch geprüft werden. Konkrete
Stärkekandidaten/Configs/Hashes und genaue Stichproben werden vor frischen
841er-Karten in einem Nachtrag fixiert, maximal zwei Kandidaten, genau ein Nominee und eine Bestätigung.
Keine Attribution eines Bündelerfolgs an einen einzelnen Bestandteil.

Vorab festgelegte Route für die zweite Alternative: Gauß nur nach vollständiger
technischer Admission plus mindestens20 strikten neuen positiven Fakten gegenüber
V∪A über mindestens5 Spiele/3 Karten und mindestens100 zusätzlichen positiven
Fakt-Schritten. Diese praktische Schwelle wird vor Gaußdaten festgelegt; sie ist
kein Siegtest und lockert keine Übernahmehürde. Andernfalls nur bei rechtzeitigem
fertigem Planungsprototyp ein kontrollierter Anpassungspilot, unveränderter Reward,
feste36-Netz-Zahl statt ein weiteres37.Netz. Dessen exakte vier Arme/Endstandwahl
brauchen vor dem Training einen eigenen Nachtrag; nichts davon ist schon gestartet.


## Präzisierung der praktischen Routingmetrik

Vor jeglicher S-Ergebnis-/Neuheitslektüre am 2026-11-02T13:34:46.897421+00:00:
20 physische positive Fakten werden konservativ als unterschiedliche
`(seed, Welt-x, Welt-y, kind)` über beide Seiten und Matches entdoppelt.
Per-Spiel-/Acquisition-Match-Zahlen zusätzlich berichten, nicht still ersetzen.
Die100 positiven Fakt-Schritte meinen den anhaltenden positiven Wissensvorsprung
von G gegenüber V∪A je Entscheidungsframe, nicht nur Neuerwerbsframes.
Mindestens5Spiele/3Karten müssen einen strikten positiven Neuerwerb enthalten.
Dies präzisiert nur die praktische Routenwahl, keine technische oder statistische
Übernahmehürde. Root und unabhängiger Auditor haben noch keine S-Zahlen gelesen.
