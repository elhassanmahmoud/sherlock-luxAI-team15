# Ensemble-Verhalten: zwei Endnetze trainiert

Beide festen ON-Läufe sind vollständig und technisch abgenommen. **Noch kein Nachweis eines stärkeren Agenten; V14 und Gruppe15.zip bleiben unverändert.**

## Was geändert wurde

Das lernende Einzelnetz bewertet während seiner Handlungen gemeinsam mit 35 eingefrorenen ursprünglichen Netzen die Aktionen. Sein aktueller Output steht an Index 18 in der ursprünglichen Reihenfolge. Reward, Exploration, Regeln und eigenes DDQN/Target/Adam bleiben gleich. Die 35 eingefrorenen Netze gehören nicht zum gespeicherten Einzelnetz-Checkpoint. Die spätere Evaluation wird beide neuen Endnetze an die ursprünglichen 36 anhängen.

Zwei feste Starts 48/49, frisch aus V14-Mitglied 18, gleiche Kontrollconfig (w_match=2, lr=0,00005, epsilon=0,05). Je 40 Vorlaufspiele mit gemeinsamer manueller Freigabe, dann 400 Lernspiele und 60.000 Updates, keine Zwischenwahl. Vorhandene ursprüngliche Kontrollfinals werden später unverändert verglichen; keine erneuten Kontrolltrainings.

## Tatsächlich ausgeführt

| Teil | Spiele | Lernupdates |
|---|---:|---:|
| Bekannte OFF/ON-Technik | 4 | 0 |
| Zwei Vorläufe | 80 | 0 |
| Zwei Lernteile | 800 | 120.000 |
| Gesamt | 884 | 120.000 |

Keine Unterbrechung oder Ersatzrunde. Beide ursprünglichen Worker und der Owner erfolgreich beendet; eigener Wachhalter ebenfalls fort. Quelle während aller Phasen unverändert `71090f760788bdcec8d7158bc5aab4fd47d406cc`.

## Geprüfte Ergebnisse

- 72 gezielte synthetische Tests vor dem ersten echten Spiel, unabhängiger Code-/Methodenreview.
- Technik: ursprüngliche Kontrollfälle exakt reproduziert, zwei ON-Fälle mit tatsächlichen legalen Präferenz-/Aktionsänderungen; 1.046 unabhängige Checks. Bekannte Niederlage dreht 1:2 auf 2:1, Kontrollsieg 3:0 wird 2:1. Diese zwei bekannten Fälle sind ausdrücklich kein Leistungstest.
- Beide Vorläufe mit 141.704 beziehungsweise 141.514 realen Replayzeilen unabhängig und durch Root geprüft; tatsächliche gespeicherte q/Target/Adam unverändert, null Updates. Gemeinsame manuelle Freigabe bindet beide Originalworker.
- Finale Prüfung: 11.298 unabhängige Checks und originale Root-Validatoren unter eingefrorener Quelle. Je 440 vollständige Chronologiezeilen, 193.320 Envschritte, 60.000 Updates; tatsächliche q/Target/alle zwölf Adamzustände endlich, jeder Adamzähler 60.000. Target am letzten Kopierzeitpunkt bitgleich q. Je 300.000 tatsächliche finale Replayzeilen geprüft. 35 eingefrorene Mitglieder unverändert nach den gebundenen Livebelegen.

| Endnetz | SHA256 |
|---|---|
| on48 | `486b9b44e12be251213b00fd84b82964c7aa5a781bdf086da866da42eb95a3fd` |
| on49 | `e0668fdcfbf70b9c85180e81af9d3bfd684b65d8aba048addee36bb58bdf27d3` |

## Grenzen und nächster Schritt

Historische vollständige Bibliotheks-/RNG-Snapshots fehlen. Gleiche alte Quellen/Interpreter-/Enginebytes und exakte OFF-Reproduktion sind belegt, aber keine universelle historische Binäridentität. Vollständige rohe Beobachtungen, alle Trainingsreward-Kontexte und sämtliche einzelnen Batchverluste sind nicht archiviert. Die 35 eingefrorenen Tensoren sind durch live berechnete Hashes und geprüften Code gebunden, kein unabhängiges zusätzliches Roharchiv. Vorläufe/Finalreplays und eigene Lern-/Optimizerarchive wurden dagegen tatsächlich geöffnet und geprüft.

Kein allgemeiner Spielstärkezuwachs, kausaler isolierter Vorteil oder 100-Prozent-Nachweis. Nächster separater Schritt ist die bereits vor dem Training feste 200er-Auswahl: BEHAVIOR38, CONTROL38, V14 gegen Solution und beide direkten Duelle. Montage/Loader und Performance separat aufnehmen; kein automatischer Übergang, Nachschlag oder V14-Ersatz.

[Root-Abschluss](operations/training-completion.json), [Finalaudit](operations/final-audit-results.json), [Vorlaufprüfung](operations/prefill-audit-results.json), [Technikprüfung](operations/technical-audit-results.json), [Plan](../../../docs/superpowers/plans/2026-11-09-ensemble-behavior.md).
