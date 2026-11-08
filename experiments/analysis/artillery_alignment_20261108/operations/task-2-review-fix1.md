# Artillery alignment — gezielte Nachprüfung Fixrunde 1

**Spec PASS / Quality PASS / technische Gesamtzulassung für den registrierten Lauf.** Der einzige offene P1 des integrierten Reviews ist behoben. Keine weiteren Befunde aus dieser begrenzten Nachprüfung.

`scripts/artillery_alignment_study.py` importiert jetzt den tatsächlichen `Belief`-Typ und projiziert ausschließlich Objekte dieses exakten Typs auf eine eindeutige Typkennung plus rekursiv aufbereitete `vars`-Felder. Damit werden der von `features.make_context` referenzierte Belief und seine Arrays/Mengen/verschachtelten Historien vom bestehenden streng typisierten Hasher verarbeitet. Unbekannte Objekte bleiben Fehler; kein allgemeiner `repr`-Fallback, keine Zustandsmutation durch die Projektion.

Die vier neuen Regressionen verwenden echten `Belief`, synthetische Beobachtung und tatsächliches `make_context`. Sie decken unveränderte/deepcopierte Kontexte, unbekannte Objekttypen sowie Änderungen an Array, Menge und verschachtelter Records-Liste innerhalb des alternativen Helpers ab. Die Mutationserkennung und Wiederherstellung von Flag/Hook passen zum ursprünglichen Befund. Der Implementer dokumentiert vier passende RED-Fehler vor Fix und anschließend 58 Studien-Tests PASS; diese Ergebnisse habe ich gelesen, nicht selbst wiederholt.

Supervisor-SHA unverändert zum ursprünglichen Review. Core→Observer→Replay→Paargate→Abschluss-/Prozessschutz-Abdeckung aus `/tmp/artillery-runner-review.md` bleibt gültig. Keine neue umfassende Reviewwelle und keine zusätzlichen Spieltests nötig. Der registrierte Vorlauf darf nach Root-Freeze-/Ressourcenprüfung beginnen; ein technisches PASS behauptet weder erfolgreiche reale Trainingsausführung noch höhere Spielstärke.

Geprüfte Hashes:

- Studie: `e02dec465f0e4ec931c5f7ad8294176b4f0cea0e57766874bbf64890160c2aeb`
- Supervisor: `1c6b37c33f5a2c2098417cf50da07b911976111a2e95a366347b7e26874e929f`
- Tests: `70787cbb76ebae54e190cb7afc41718d63d8e93ef175f297e5eeb64ed42d2711`

Nur gezielte statische Nachprüfung. Null eigene Tests, Spiele, Modellvorwärtsläufe oder Lernupdates; keine Repositoryänderungen.
