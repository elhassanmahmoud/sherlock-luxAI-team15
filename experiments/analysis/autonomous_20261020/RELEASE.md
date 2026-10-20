# Übernahmeprüfung: all18_v3 gegen old3_sym3

Stand: 20.10.2026. Die Spielmessung ist vollständig und erfüllt die vorab
festgelegten Stärkekriterien. Checkpoint-Prüfung, Reproduktion nach Integration
und Testsuite sind bestanden; Installation und anschließende Kursprobe sind
in diesem Zwischenstand noch offen.

## Vergleich auf neuen Karten

Vorab ausschließlich für diesen Vergleich reserviert: **502420–502619**,
200 Karten, beide Seiten, je 400 Spiele pro Agent und Gegner. Drei Matches
pro Spiel, Punktemessung Version 2, keine Exploration oder Gewichtsänderung.
Messcode: `14d239fc2c55bca02fb9bb6ddf3e380ca554f0d5`.

| Gegner | Alte Abgabe old3_sym3 | Kandidat all18_v3 | Differenz | 95%-Intervall der Differenz |
|---|---:|---:|---:|---:|
| Default | 382/400 (95,5 %) | 400/400 (100 %) | +4,50 Prozentpunkte | +2,00 bis +7,50 |
| Solution_92 | 170/400 (42,5 %) | 313/400 (78,25 %) | +35,75 Prozentpunkte | +29,00 bis +42,25 |

Keine Unentschieden. Kennzahl ist mittleres `result` (Sieg 1, Remis 0,5,
Niederlage 0); hier entspricht sie der Siegquote. Gepaarter Bootstrap über
ganze Karten einschließlich beider Seiten, 5.000 Wiederholungen, Zufallsseed 0,
95%-Perzentilintervall. Die Default-Bedingung war höchstens zwei Prozentpunkte
beobachteter Rückgang, kein formaler Nichtunterlegenheitstest.

## Direktvergleich

Auf den bekannten 60 Entwicklungskarten 500720–500779, beide Seiten:
**96 Siege, 24 Niederlagen, keine Remis**, mittleres Ergebnis 80 %,
Karten-Bootstrap-Intervall **70–90 %**. Gegner war ausdrücklich die gesicherte
alte Datei, nicht ein veränderlicher Abgabepfad.

Vor Einsicht in dieses Ergebnis festgelegte Zusatzbedingung: untere Grenze
strikt über 50 %; Überschneidung wäre unklar und hätte die automatische
Übernahme verhindert. Bestanden. Diese wiederverwendeten Karten sind keine
weitere unabhängige Generalisierungsstichprobe.

## Was daraus folgt

Mahmouds bereits vorhandener Kandidat V3 ist in diesem Vergleich klar stärker
als die bisher installierte Abgabe. Das ist **kein Nachweis eines neuen
Codex-Trainingsgewinns**: Die zusätzliche Suche nach Energiereserve und
Zielreichweite brachte keinen gewählten Herausforderer (siehe DEVELOPMENT.md).
Der Vergleich isoliert außerdem weder Netzanzahl, Trainingsänderungen noch
einzelne Regeln; der gesamte Agentenstand wird verglichen.

V3 verliert weiterhin 87/400 Spiele gegen Solution_92. Die Ergebnisse sind
keine Garantie gegen unbekannte Gegner, auf jeder Karte oder unter einer
anderen Kurskonfiguration. Intervalle erfassen Kartenstreuung für diese festen
Agenten und Gegner, nicht unterschiedliche Trainingsstarts.

## Quellen und Reproduktion

- `release_evidence.json`: geprüfte Kriterien, Intervalle, CSV-Hashes,
  Sicherungsidentität und Grenzen.
- `release_check_state.json`: vollständige Befehle und Jobstatus.
- `../../compare/autonomous_20261020/release_old.csv` und `release_v3.csv`:
  je 800 Spielzeilen.
- `../../compare/autonomous_20261020/v3_vs_old.csv`: 120 Direktspiele.
- `sync_smoke.csv` im selben Vergleichsordner: acht identisch reproduzierte
  Entwicklungsspiele; reine Integrationskontrolle.

Gepaarte Vergleichsauswertung aus dem Repo-Hauptverzeichnis:

```bash
.venv/bin/python -m scripts.compare_report \
  --ref experiments/compare/autonomous_20261020/release_old.csv \
  experiments/compare/autonomous_20261020/release_v3.csv
```

Eine erneute Spielausführung muss neue Ausgabepfade benutzen. Die Befehle im
Statusbericht enthalten historische absolute Pfade von Moayeds Rechner;
auf einem anderen Rechner durch den jeweiligen Repositorypfad ersetzen.
Die lokale `.gitattributes` im Vergleichsordner verhindert Git-Zeilenenden-
Umwandlung dieser CSVs: Audit-Hashes beziehen sich auf ihre exakten Bytes.

## Sicherung und technische Freigabe

Unveränderliche Sicherung: `experiments/releases/20261020_old3_sym3/`, inklusive
Manifest und Wiederherstellungsanleitung. Alter Hash beider Dateien:
`3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
V3-Quellhash:
`aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.

Vor Installation bestanden: explizite Prüfung aller geladenen Netzparameter
und Configs beider Stände, Reproduktion von 16 bereits ausgewerteten Spielen
nach Integration bis `3a4f32f` (siehe `final_release_checks.json`), vollständige
Testsuite mit **169 Tests in 46,44 s**. Die zusätzlichen Pfade `cand_boost` und
`contest_sap` sowie `pt_walk` sind in beiden effektiven Configs deaktiviert.
Nach Installation: Hashkontrolle beider Abgabedateien und Kursprobe mit dem
unveränderten Professor-Runner. Bei Fehlern keine Freigabe beziehungsweise
Rückkehr zur gesicherten alten Abgabe.
