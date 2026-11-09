# Vergleichswerkzeuge: Umsetzung und tatsächliche Prüfung

Nur drei neue Projektdateien umgesetzt: `scripts/threat_warmstart_compare.py` (433 Zeilen), `scripts/threat_warmstart_compare_owner.py` (115), `tests/test_threat_warmstart_compare.py` (261). Bestehender Agent, Gewichte, Pläne und historische Studien unverändert; kein Commit oder Push. Grundlage ist der verbindliche Plan `docs/superpowers/plans/2026-11-09-threat-warmstart-comparison.md`.

Montage ersetzt ausschließlich Mitglied 18, hält die anderen 35 geordnet und bytegleich und prüft gespeicherte sowie tatsächlich geladene Zustandsdictionaries. Nur akzeptierte Endmodellhashes, genau 36 Mitglieder, ursprüngliche V14-Inferenzkonfiguration plus die festgelegten Schalter. Historische Trainingsaufnahme und tatsächliches Root-Closure-Schema werden getrennt von der neuen Vergleichsquelle geprüft; ursprüngliches `validate_final_receipt`, kein altes `admission()` gegen neuen HEAD. Historischer Owner-State und dessen beide Receipts müssen gebundene Eingaben sein.

Technik und Performance bleiben getrennte Aufnahmen. Technischer Worker prüft gleiche 101er-Formen, die ersten 16 exponierten Folgezustände, die drei Batchgrößen und vier bekannte Stock-/Nulladapter-Ausführungen auf einer wiederverwendeten Umgebung. Performance ruft ausschließlich vorhandenes `par_eval --workers 1` in fünf festen 40er-Blöcken auf. Die drei vorab festgelegten Kartenlisten werden exakt geprüft. Guard, Prozessbesitz, atomare JSON-Veröffentlichung, Statistik und gezieltes Cleanup bleiben bestehende Hilfen. Nach beendetem Launcher wartet der Owner maximal zehn Sekunden auf dessen eigene Pool-/Tracker-Gruppe, prüft weiter den Guard und sendet während dieses Wartens keine Signale. Fehler werden vom bestehenden ausschließlich eigenen Cleanup behandelt. Unbekannte unterbrochene Teilspielzahlen werden ausdrücklich so bezeichnet.

**Tatsächlich ausgeführt:** Zuerst ein numerischer Regressionstest gegen den bisherigen Textentwurf: `red-argmax.log`, Exit 1, 1 erwarteter Fehler. Mit allen legalen Q-Werten unter −10⁹ wählte dessen endliche Maskenersetzung eine unzulässige Aktion. Umsetzung jetzt wie Core mit `-inf`. Der temporäre Textloader wurde anschließend aus den Tests entfernt. Zweiter gezielter Fehlnachweis `red-first-rows.log`, Exit 1, 1 erwarteter Fehler: eine ungültige Maske unter den ersten 16 exponierten Zeilen wurde vorher durch spätere Zeilen ersetzt. Jetzt strikte Auswahl und Abbruch.

Finaler gezielter Aufruf: `env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_threat_warmstart_compare.py`. **Exit 0: 20 passed in 2.07s**, Originalausgabe `final-tests.log`. Zusätzlich alle drei neuen Dateien mit `git diff --no-index --check /dev/null DATEI` geprüft: jeweils Exit 1 bei neuen Dateien gegenüber `/dev/null`, keine Leerraumdiagnosen/Ausgaben. Keine breitere Suite ausgeführt.

Die synthetischen Tests decken Montage/Reihenfolge/36 statt 37, falsche Formen/Dtypes/Config, Nullspaltenkontrast, echte künstliche Tensorforwards und Legalmasken, feste Karten/Jobs, historische Abschlussübergabe, Ergebniszeilen und tatsächliche Sieg-Gates, exklusive Ausgaben/Bindungen sowie begrenztes eigenes Prozessende ab. `torch.load` ist in diesen Tests gesperrt. Der historische Modellvalidator ist in seinem Schnittstellentest ausdrücklich ersetzt, da echte Archive Root vorbehalten bleiben.

**Grenzen:** Keine tatsächlichen Endmodelle oder V14-Archive geladen, keine realen Spiele, kein echter Pool-/Engine-Prozess gestartet. Tatsächliche Loader-/Batch-/Spielgleichheit und der vollständige überwachte CLI-Lauf sind erst durch Root aufzunehmen. Der Bericht behauptet keine Stärke und keine bereits bestandene reale Technikprüfung. Technische Digests dokumentieren live verglichene Verläufe; sie ersetzen keine archivierten Rohbeobachtungen. Große Replays bleiben gebundene lokale Eingaben.

SHA256:

- Vergleich: `cbffceb856a3ba62e2668d585222051c88f6f5c6e6f00eebae370ff89d95f5e7`
- Owner: `57d49a1129d7e018b1bf21ffb07f7f4ccdc8f091ffd1b3d3fef04046fc9f26f5`
- Tests: `2e621cf9855283b12b3271f0e11ea21835b76199fa947df26818e0f07048a641`
- Finaler Testlog: `a5fb2e78943c7d5e7bd4ed42832803794b39bd69b087bd917ec0b89ef831c1dc`
