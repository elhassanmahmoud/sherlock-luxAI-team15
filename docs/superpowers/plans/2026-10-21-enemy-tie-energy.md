# Einzelvergleich: Energie bei gleich nahen Gegnern

## Entscheidung vor Ergebnisbeobachtung

Autonomer Folgeversuch im weiterhin autorisierten Verbesserungsauftrag. Anlass ist der [begrenzte Repräsentationscheck](../../../experiments/analysis/continuous_20261021/representation_probe/README.md): zwei sichtbare tatsächlich konvergierende stärkere Gegner werden in der nächsten-Gegner-Auswahl durch gleich nahe schwächere Gegner verdrängt. Der Informationsverlust ist im tatsächlichen Featurecode gezeigt, eine bessere Entscheidung/Siegquote nicht. Die kleine Änderung testet genau diese Auswahl; sie ist kein allgemeiner Schutz gegen Kollisionen.

Andere Ansätze wurden abgewogen: eine größere Gegnerdarstellung erfordert neue Featuredimension/Training; ein pauschales Bewegungsverbot greift direkt in Aktionen ein und ähnelt schon negativ getesteten Masken. Hier bleibt die bestehende79er-Eingabe, und die trainierten Netze entscheiden weiterhin. Die Verteilung ihrer Eingaben kann sich trotzdem ändern und schlechter werden; deshalb nur ein abwählbarer Versuch.

## Genau eine Variante

`enemy_tie_energy` bool, Standard false und bei alten Checkpoints false. In `make_context` weitergeben; in `build_features` bei true nur unter Gegnern mit minimaler Manhattan-Distanz die höchste sichtbare Energie auswählen. Gleichstand auch bei Energie: ursprünglicher erster Eintrag. Keine Filteränderung für negative Gegnerenergie, keine Änderung von Gegnerzählern, Zielzuweisung, Masken, Aktionen, Netzdimension, Reward oder Training. Fehlender Kontextschlüssel verhält sich wie false.

Basis ausschließlich eingefrorenes V3, SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`. Kandidatencontainer unterscheidet nur diese explizite Configoption; alle18 Q-Netzidentitäten bleiben unverändert. Keine Kombination mit einem möglichen Curriculumkandidaten, keine weitere Tiebreak-/Featurevariante nach Ergebnisbeobachtung.

## Isolation und technische Zulassung

Vorbereitung in eigener Arbeitskopie `sherlock-enemy-tie`, Branch `improvement/enemy-tie-20261021`; eingefrorenes laufendes Curriculum bleibt unberührt. Während dessen Training nur NumPy-/Stdlib-Tests und Quellreview, keine Modellimporte/-audits oder zusätzlichen Spiele. Native Worktree-Anlage war wegen übergeordnetem nicht-Git-Arbeitsordner nicht verfügbar; normale Git-Arbeitskopie erstellt.

Vor dem ersten Spiel: unabhängiger Review, passende Integrationstests nach Ende des Trainings, sauberer Quellen-/Plan-/Interpreter-/Enginefreeze, drei Matches, V3- und Sicherungshashes, exklusiver frischer Ausgabepfad. Keine Abgabeänderung durch Tests. Bei standardmäßig false müssen bekannte Referenzspiele unter dem neuen Quellstand exakt reproduziert werden; Nichtzeitfelder und Punktezählversion2,303Schritte, genaue vollständige Schlüssel kontrollieren. Hashidentität der18Q-Netze und Configdifferenz vor/nach Auswertung prüfen. Pro Job maximal zwei Evalworker, keinerlei Paralleltraining.

## Feste Folge und Gates

1. Entwicklung: V3 und V3+enemy_tie_energy, je60 bekannte Karten500720–500779 × beide Seiten × default/Solution_92 = je240, zusammen480 Spiele. Kein Checkpointtraining oder weitere Varianten. Referenz-Nichtzeitwerte gegen vorhandene V3-Entwicklungsdaten abgleichen.
2. Nur bei positiver gepaarter Sol-Differenz UND unterer95%-Kartenbootstrapgrenze>0 sowie Defaultdifferenz≥−2Prozentpunkte: neue Karten522000–522199, beide Seiten/beide Gegner, je800, zusammen1600Spiele. Gleicher Vorteils-Gate.
3. Nur danach direkt Kandidat gegen V3 auf neuen Karten522200–522399, beide Seiten,400Spiele. Untere95%-Grenze des über Kartenpaare gemittelten Kandidatenresultats muss strikt>0,5 sein.

Immer vollständige Schlüssel und finite gültige Resultate0/0,5/1 prüfen; Gates über exakte Halbresultateinheiten, keine Rundung. Bootstrap ganze Kartenpaare,5000Ziehungen/Seed0, Perzentile2,5/97,5. Keine Stichprobenverlängerung, kein Poolen historischer Daten. Negative Gates beenden genau diese Variante, Teilstände sind keine statistische Ablehnung. [CSV-Kollisionsprüfung](../../../experiments/analysis/continuous_20261021/representation_probe/seed_reservation.json) ohne Treffer; vor frischer Nutzung Remote erneut prüfen. Curriculum511000–511399 und finaler Audit520000–520999 bleiben getrennt.

Alle Folgephasen konservativ zeitlich zulassen: feste Obergrenze zwei Stunden ab tatsächlichem Start dieses Vergleichs, maximal beobachtete Ensemblezeit pro Spiel×1,25 für alle möglichen restlichen2480Spiele plus15Minuten technische Reserve. Bei unzureichender Reserve nicht starten/sauber abbrechen, keine Spielzahl kürzen. Die Obergrenze ist eine Ressourcenentscheidung, kein Deadlineersatz des Benutzerauftrags.

## Übernahme und Grenzen

Ein statistisch qualifizierter Kandidat braucht anschließend Kurs-/Import-/Lade-/Legalitäts-/Laufzeit-/Paket- und Reproduktionsprüfung. V3 vor Übernahme zusätzlich versioniert sichern; alte6-Netz-Sicherung erhalten. Falls inzwischen ein anderer Kandidat die Abgabe ersetzt hat, ist ein Sieg gegen V3 KEINE Übernahmefreigabe gegen diesen neuen Stand: separat vorab festgelegter Vergleich mit dann neuen Karten erforderlich. Kein Zusammenschalten zweier Varianten aus getrennten Erfolgen.

Noch keine Spielresultate oder Übernahme. Ein endlicher1000-Karten-Abschlussaudit bleibt ausschließlich für den zuvor qualifizierten eingefrorenen endgültigen Kandidaten reserviert;100%universell bleibt unbewiesen. Dieser Plan ändert keine Gates oder Quellen der laufenden Curriculumstudie.
