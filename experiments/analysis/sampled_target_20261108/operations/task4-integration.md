# Tatsächliche Aufnahme der Leistungswerkzeuge

Root, 08.11.2026. Der [Entwurfsreview](task4-draft-review.md) ist historisch und hatte keine Tests ausgeführt. Danach wurde die wirkliche Trainingsabnahme gebunden. Root hat tatsächlich **32 synthetische Tests, Exit 0, 3,60 Sekunden** ausgeführt: vollständige400-Spiel-Matrix, Ganzzahlgrenzen einschließlich Remis, gepaarter Kartenbootstrap, historische Hashkette sowie beide tatsächlichen Agent-/self-Ladewege mit identischen Einstellungen. Keine Spiele aus pytest.

[Maschinenlesbarer Testbeleg](task4-tests.json). Nach dem Test wurden nur zwei veraltete Vorbereitungs-Docstrings aktualisiert; kein erneuter Testlauf dafür. AST-Abgleich mit dem vollständig unabhängig gelesenen Entwurf: ausführbare Logik unverändert, außer dem vorgesehenen tatsächlich akzeptierten Trainingshash.

Anschließend tatsächlicher Build/Reload der vier Inferenzkopien aus den vollständigen Endnetzen, alle Nicht-Config-Inhalte identisch. Beide Seiten verwenden dieselbe gebundene V14-Quellkonfiguration, mit ausschließlich frozen=False. Ursprüngliche Trainingsdateien unverändert. Der strikte historische Aufnahmeweg hat die echten versiegelten Daten akzeptiert; exakt zehn Jobs/400 Spiele erstellt.

Noch keine Leistungsdaten. Start erst nach Commit, sicherem Remote-/Lokalabgleich und neuer Quellenbindung; keine zusätzliche Auswahl, Zwischenstände, V14-Rolle oder Übernahme. Der vorbereitete unabhängige Leistungsauditor bleibt bis zum vollständigen Ende UNRUN.
