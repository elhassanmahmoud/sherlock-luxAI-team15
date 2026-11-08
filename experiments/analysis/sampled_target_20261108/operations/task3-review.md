# Unabhängiger statischer Task3-Review

**Ergebnis: PASS_STATIC – keine konkreten Blocker in der geprüften Fassung.**

08.11.2026. Ausschließlich lesende Prüfung im Studiencheckout bei HEAD `49104d138aa82662bb1610fe8db3d6cda0e1fa44`. Keine Imports, Tests, Modelle, Spiele oder Git-/Repoänderungen durch diesen Review. Dieser Befund ersetzt weder die Root-Aufnahme noch die noch ausstehenden vier echten technischen Integrationsspiele und ist kein Laufzeit- oder Wirkungsnachweis.

## Geprüfte Fassungen

SHA-256, selbst aus den tatsächlich gelesenen Repo-Dateien ermittelt; die drei Implementierungshashes stimmen mit der vom Implementer eingefrorenen Fassung überein:

| Datei | SHA-256 |
|---|---|
| `scripts/sampled_target_study.py` | `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224` |
| `scripts/sampled_target_supervisor.py` | `df85b767962cffc9c903da86b4ac4f539143ef7b0b0faa24f21e017c2687d07d` |
| `tests/test_sampled_target_study.py` | `ea0c80d1c7c8cf8e89bf130cc7fbad0088c0a1bf8ec83e5d41bd4934d3ce8469` |
| `docs/superpowers/specs/2026-11-08-sampled-target.md` | `0b3e86ca7e1ca2559f9001343f8c8073127d5d46c363ec761500964e8ae91a2d` |
| `docs/superpowers/plans/2026-11-08-sampled-target.md` | `2649209104db363c8b5fb0efcfdf6cb5ccaf8a4de27957abe86159f351b44d34` |

## Wesentliche Prüfpunkte

- **Technik vor Frischstudie:** `technical_plan`, `validate_admission`, `validate_technical_receipt` und `compare_technical_receipts` binden genau Kontroll-/Sampled-Modus × beide Seiten auf bekannter Karte4242 gegen default, Anker45, jeweils303 Schritte und null Updates. Die Studienaufnahme verlangt vier geprüfte technische Receipts und beide Seitenvergleiche; keine automatische Weiterleitung vom technischen Supervisor in das Training.
- **Fester Umfang:** Vier Arme, Starts45/46, jeweils40 Vorlauf- und160 Lernspiele mit identischer exogener Paarfolge und getrennten festen Kartenkohorten. Die Endprüfung verlangt200 Spiele,24.000 Updates und120.600 Env-Schritte pro Arm. Task4-Leistungsspiele werden hier weder gestartet noch als bestanden dargestellt.
- **Folgeaktion und Replay:** `EventValidator`, `validate_stream` und `validate_phase_bundle` prüfen Capture-/Commit-Reihenfolge, eindeutige Übergänge, spätere bestätigte Framebindung derselben Unit/Episode/Matchgrenze, kanonisches Label, Features/Masken und Zählerzeitpunkt. Terminalzeilen verwenden die festgelegten Sentinels. Der komplette Vorlauf wird mit gespeicherten Replayzeilen verbunden; beim Endpuffer werden alle gespeicherten Ringzeilen gegen das vollständige Ereignisprotokoll geprüft. Keine Gleichsetzung eingereichter Befehle mit garantierter Enginewirkung.
- **Paargate vor Gradienten:** Beide vollständigen Vorläufe müssen einschließlich Trajektorien, Rewards, Replay, RNG und unveränderter Q-/Target-/Adam-Zustände übereinstimmen. Die deterministische Diagnose benötigt mindestens eine Index- und eine Targetwertabweichung und prüft unveränderte Lern-/RNG-/Replayzustände. Worker lesen die Rohbelege erneut, bevor `learn_enabled` gesetzt wird. Die native Aktionskette und `_update` werden nicht kopiert; produktive Coredateien bleiben außerhalb der Änderung.
- **Atomare Bereitschaft:** `write(exclusive=True)` serialisiert vorab, schreibt und synchronisiert die temporäre Datei und veröffentlicht sie exklusiv mit `os.link`. Der zugehörige Test deckt den Serialisierungsfehler und Überschreibschutz ab. Auch das Paargate wird erst vollständig veröffentlicht.
- **Betrieb und Abbruch:** Quellen-/HEAD-/Plan-, Eingabe- und V14/ZIP-Bindungen, frischer Kontingentbeleg, AC, Threads1, Fremdprozessprüfung und maximal zwei registrierte Worker sind vorgesehen. Startregistrierung ist zeitlich begrenzt und an PID/PGID/Parent/Befehl gebunden. Paare laufen nacheinander. Fehler führen zu STOP/unvollständigem Status; der wiederverwendete Cleanup signalisiert ausschließlich eigene Prozessgruppen. Kein automatischer Wiederholungsweg.

Die synthetischen Tests wurden vollständig als Text geprüft, insbesondere falsche Labels/Replayfelder, unvollständige Ereignisse, Nullintervention, fehlerhafte Aufnahme, feste Technikbefehle, Markerpublikation, Eigentumsregistrierung und Cleanup. **Dieser Reviewer hat keine Tests ausgeführt.** Root und Implementer melden separat den finalen gemeinsamen Lauf mit123 bestandenen Tests in3,19s; deren Ausführung wird hier nicht als eigene Prüfung ausgegeben.

Offen bleiben die ausdrücklich vorgesehenen realen Aufnahmebedingungen und technischen Integrationsbelege. Aus dem statischen Task3-Scope ergibt sich kein zusätzlicher Änderungsbedarf.
