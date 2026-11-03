# Unveränderte V14-Abgabe: zusätzliche Technikprüfung

Alle vier Stufen bestanden nach Reparatur der isolierten 3.10-Umgebung.
Keine neue Stärkeauswertung, kein P-Release und kein Gewichtstausch.

| Stufe | Nachweis | Neue Vollspiele |
| --- | --- | ---: |
| `runner310` | Acht Kurs-Runner-Spiele, je 303 Schritte, Modelle geladen | 8 |
| `zip310` | Zwei Ordnerpositionen; API, erster Schritt, `train=True` eingefroren | 0 |
| `record313` | Reales 303-Schritte-Spiel der bestehenden ZIP, Seed 4242 | 1 |
| `replay310` | Dieselben Beobachtungen, 606 Entscheidungen, 0 abweichende Aktionen | 0 |

`process.json`, `runner310.json` und vier Logs belegen die Ausführung.
`existing_zip_payload.json` vergleicht die 36 geordneten Float32-Netze und alle
anderen Checkpointfelder exakt mit V14: Nur `cfg.frozen=True` wird im Paket
ergänzt. Die 14 Laufzeitmodule stimmen mit Git 75af0c5 überein. Die 18 ZIP-Einträge
enthalten keine internen Repo-Dokumente. ZIP 88dfbe32…9dff9d6 und Raw-Gewichte
98a07350…d3d8 blieben unverändert.

Umgebung: macOS arm64, Python 3.10.22/Torch2.2.2/NumPy1.26.4, Engine 0.2.1 und
bestehende Kurskonfiguration mit drei Matches. Der Replayvergleich gilt für das
gespeicherte Spiel. Kein Windows-Test oder Nachweis einer unbekannten Zeitgrenze.
Aktionsmediane je Spiel 13,0–17,7 ms, Maximum 39,2 ms.

Der erste Versuch scheiterte vor Spielen am SciPy 1.15.3-Mach-O-Wheel.
`py310_repair_report.*` und `repair_evidence/` belegen die isolierte Reparatur auf
ein offizielles SciPy 1.14.1-Wheel. Alle 59 anderen Distributionen, zehn gebundenen
Engine-Pythondateien, aktive Abgabe und gemeinsames 3.13 blieben erhalten. Erst
nach bestandenen Bibliotheksimporten liefen die tatsächlichen Agententests.

Unabhängiger Review PASS für diesen dokumentierten Umfang, siehe
`V14_py310_final_review.*`. Historische Grenzen: Der Launcher speicherte Befehle,
Laufdauern und geschützte Hashes, jedoch keine separaten Startzeit-/cwd-/Source-
Snapshots pro Stufe. Der Payload-Vergleich lief inline im Root-Toolaufruf;
ein damals gespeicherter Producer existiert nicht. Diese fehlenden historischen
Startnachweise werden nicht rückwirkend ergänzt.

`v14_4242.pkl.gz` ist verlustfrei komprimiert; beide Hashes stehen in
`archive_provenance.json`. Zum Nachspielen in eine neue temporäre `.pkl` entpacken
und das versionierte `scripts/xversion_replay.py replay` verwenden. Pickledaten
nur aus vertrauenswürdiger Herkunft laden. SciPy-Wheeldateien sind nicht im Repo;
öffentliche Quelle und genaue Hashes stehen im Reparaturbericht. Historische
JSON-Dateien mit absoluten Pfaden unverändert lassen.
