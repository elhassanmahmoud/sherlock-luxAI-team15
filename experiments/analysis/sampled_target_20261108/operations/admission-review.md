# Unabhängige Aufnahmeprüfung: Sampled-Target-Pilot

08.11.2026. **PASS im beauftragten Umfang; keine offenen Aufnahmeblocker in den geprüften Unterlagen und Belegbindungen.** Dies ist ausdrücklich **keine Startfreigabe**, keine Abnahme des noch entstehenden Task-3/4-Runners und keine Aussage über Spielstärke oder einen V14-Ersatz.

Geprüft wurden die aktuelle Spec/der Plan, Methoden- und Task-1/2-Fixreviews, der historische 53-Testbeleg sowie die vollständige Seed-Abnahmekette einschließlich Rohgzip. Ausgangs-HEAD dieser Arbeitskopie: `9a022923b78c93664445dd350bc86aaaf5a1d635`. Projektregeln und jüngster Arbeitsstand wurden gelesen. Es liefen ausschließlich Text-/JSON-/gzip-/Hashauswertungen mit Standardbibliothek und lesende Gitabfragen: kein Projekt-/Torchimport, Test, Modell, Spiel, neuer Vollscan oder Repoeingriff. Einzige eigene Ausgabe ist dieser Bericht unter `/tmp`.

## Kohorten und unveränderter Umfang

Alle sechs Arrays in `seed_acceptance.json` stimmen elementweise und in Reihenfolge mit den inklusiven Rohscanbereichen und der Spec überein:

| Kohorte | Exakte inklusive Spanne | Karten |
|---|---|---:|
| prefill45 | 9915000–9915019 | 20 |
| train45 | 9910000–9910079 | 80 |
| prefill46 | 9925000–9925019 | 20 |
| train46 | 9920000–9920079 | 80 |
| panel | 9930000–9930019 | 20 |
| direct | 9930100–9930119 | 20 |

Zusammen exakt 240 verschiedene, untereinander disjunkte Karten. Starts 45/46; beide Seiten; je Arm 40 Vorlauf- und 160 Lernspiele. Das ergibt 160 Vorlauf- plus 640 Lernspiele = 800 Ausführungen, 24.000 Updates je Arm und 96.000 insgesamt. Die vier finalen Einzelnetze erhalten je 80 Panelspiele, die zwei Startpaare je 40 Direktspiele: 400 Leistungsspiele. Genau vier zusätzliche technische Ausführungen auf der ausdrücklich bekannten Karte 4242 (zwei Modi × zwei Seiten, default, keine Gradienten), insgesamt höchstens 1.204 vollständige Ausführungen. 4242 liegt außerhalb aller Frischekohorten; Rohscan und Root-Abnahme deklarieren dafür ausdrücklich keine Frische.

Kein V14-Leistungsvergleich, Ensemblebau, automatischer Nachschlag oder Abgabeersatz ist Teil dieser Methode. Die technischen Ausführungen verwenden nun ausdrücklich den festen Initialisierungsanker `run_seed45`; alle vier Agenten bleiben frisch, und technische Puffer sind keine Studienstartpuffer.

## Vollständige Hashkette und Rohbefunde

Folgende Bindungen wurden an den tatsächlich vorhandenen Bytes neu nachgerechnet:

- `seed_acceptance.json`: `a6af331d0d4c0924bfb31649f9b4c921a303fd3a2a67f394737a3db2785fd8bb`.
- Darin gebundener Root-Audit `seed-audit-acceptance.json`: `f41a55f3e5d101413a218489893b92633b48e658df6f2d17ad654820a3e56d2f`.
- Darin gebundenes `seed-audit.raw.json.gz`: `24bfcbb9d8f7e1ced08a1585074a8073e953a1c447e79db18251af10d34ac1f4`.
- Dekomprimiert exakt 17.721.156 Bytes, SHA-256 `48c906a80d274f32ac2df7ac6bef5de10a64e753bd97557fac3e7fc768fca7a7`. Zusätzlich bytegleich zum noch vorhandenen Original `/tmp/sampled-target-seeds/seed-audit.json`; kein Verlust durch Archivierung.
- Gebundener Auditor: `f29a816897c411c8e7c133847b5f3793ca85e037a7a549fd8093ff0b64da6b4d`, sowohl zur aktuellen Datei als auch zum im Rohbericht aufgezeichneten Skripthash passend. Gebundener Kurzbericht `seed-audit.md`: `888e287ca59cdac89de3770da789505b1ba1b36eb987ca5d528b3097b82fefe7`.

Der Rohbericht enthält exakt acht erwartete Worktrees; die aufgezeichneten HEAD-Mengen vor und nach dem Scan stimmen vollständig überein. 15.487 strukturierte und 9.012 Textpfade sind ohne doppelte Pfadzeilen vorhanden. Inventarzähler, SHA-basierte Dubletten und eindeutige Inhaltszahlen wurden aus den Listen unabhängig nachgezählt: 1.685 CSV-, 391 JSONL- und 1.417 JSON-Inhalte sowie 1.759 Textinhalte. Die 712 gespeicherten Intervallkandidaten haben rechnerisch keine Überschneidung mit den sechs Zielbereichen. Alle gespeicherten Listen für Verbrauchs-/Zahl-/Intervall-/Texttreffer, Fehler, Textdekodierlücken und Mutationen sind leer; keine Repositoryreservierung ist per Allowlist ausgeblendet.

Alle zwölf `json_string_mentions` wurden einzeln gegen die zwei darin benannten historischen Originalarchive aufgelöst. Deren aktuelle gespeicherte Bytes stimmen mit dem jeweiligen Rohinventarhash überein. Jede Fundstelle ist tatsächlich ein `text_files[…].sha256`-Feld mit demselben vollständigen 64-stelligen Hexdigest `b7ced60b36f511b2118f24d5cea70e41802a9910072af665d74e0ba137b4e07d`; `9910072` ist ausschließlich dessen Teilstring. Keine dieser zwölf Fundstellen ist eine Seeddeklaration oder ein Verbrauchsbeleg. Die Rohbefunde bleiben vollständig erhalten.

Das interne Rohberichtsfeld `duration_seconds` beträgt 57,32880733394995 Sekunden. Die übermittelte Angabe rund 57,38 Sekunden kann die äußere Ausführung einschließlich abschließender Ausgabe bezeichnen; aus dem Rohbericht selbst wird hier nur der gespeicherte interne Wert behauptet. Das ist kein fachlicher Blocker.

## Methodischer Entwurf und finale Dokumentfassung

Die aktuellen `/tmp`-Dokumente enthalten bereits die vier im Methodenreview verlangten historischen Statuskorrekturen. Diese vier eng definierten Textänderungen wurden ausschließlich im Speicher rückgängig gemacht. Dadurch entstehen **exakt** die im Methodenreview gebundenen Ausgangshashes:

- Spec: `2c99912b1db2c601c14cdfa4681c494290ca385394638918574434a1f9517b94`.
- Plan: `c290ffebea23ce083c50021c1ef44c189535faba2294994b093055b5e3417a02`.

Damit ist die Differenz zum tatsächlich methodisch geprüften Stand nachvollziehbar: vier Statuspräzisierungen; danach in der Repo-Spec ausschließlich portable Repositorylinks und der explizite technische `run_seed45`. Der Repo-Plan ist bytegleich mit der statuskorrigierten `/tmp`-Fassung. Sämtliche neun lokalen Dokumentlinkziele existieren. Weder Hypothese, Targetformeln, verzögerte Replayfreigabe, Vorlaufgate, Kohorten, Lernumfang noch Leistungsgates wurden darüber hinaus verändert.

Aktuelle geprüfte Dokumenthashes:

- `docs/superpowers/specs/2026-11-08-sampled-target.md`: `0b3e86ca7e1ca2559f9001343f8c8073127d5d46c363ec761500964e8ae91a2d`.
- `docs/superpowers/plans/2026-11-08-sampled-target.md`: `2649209104db363c8b5fb0efcfdf6cb5ccaf8a4de27957abe86159f351b44d34`.
- `operations/method-review.md`: `ee10ec802aa8156509a19117d4af8f7aa82509161cd39422363979cba501aa7f`.

## Bindung an den tatsächlich aufgezeichneten Task-1/2-Test

Die installierten Dateien sind bytegleich mit den im statischen Fixreview und im Root-Testbeleg gebundenen Fassungen:

- `scripts/sampled_target_agent.py`: `c767ee07a6fcf9566e762e105eec36a3b51e44664cb1b4b77e82d93ddd414bf9`.
- `tests/test_sampled_target_agent.py`: `020819bc80df0b1ff81d4c390110bf8ca13fbff84ee74f54636d3625252657eb`.

`task12-tests.json` hat SHA-256 `9f374a6c64fd399642cbe2a7ac7d0aef47fb4044ab25e1fe781d57f7b796b85d` und dokumentiert den Root-Aufruf mit 53 bestandenen Tests, 2,71 Sekunden, Exit 0, Toolsession 79353, damaligem HEAD `cb8dea5440d9369d60c4e42f4c0bbaaa7bcd9b34`. Dieser Review bestätigt die Bytebindung an diesen vorhandenen Beleg; er wiederholt die Tests nicht und behauptet keine eigene Beobachtung des historischen Testprozesses. Die im Beleg genannte fehlende vollständige eingefrorene Umgebungsinventur bleibt eine Grenze. Die älteren UNRUN-Berichte sind korrekt als historische Vorstufen erhalten.

## Aussagegrenzen und weiterhin offene Aufnahmebedingungen

- Die Frischeaussage lautet ausschließlich „keine beobachtete andere Verwendung/Reservierung im begrenzten lokalen Audit“. Die aus den Rohlisten nachgerechneten Lücken bleiben: 286 CSV- und 228 JSONL-Dateien ohne numerischen Seedbeleg, 338.472 JSONL-Records ohne numerischen Seed sowie 1.328 ungültige nichtleere Seedwerte. Kein gespeicherter ungültiger Wert enthält einen Zielbereichstoken; damit ist seine unbekannte Bedeutung nicht aufgelöst.
- Externe Rechner, unregistrierte Kopien, undokumentierte Spiele, unbekannte Schemas, errechnete Formeln, opaque Binärdateien, ausgeschlossene Ordner und nicht verfolgte Verzeichnissymlinks bleiben außerhalb des Nachweises. Neu angelegte Textdateien werden im Auditor nicht erneut vollständig inventarisiert. Die Root-/Watcher-Stabilitätsbestätigung ist eine dokumentierte Betreiberbestätigung, kein unabhängiger Beweis durch den CLI-Schalter.
- Dieser Review rekonstruiert die gespeicherten Scanbelege und ausgewählte darin benannte Quellen; er scannt die acht Arbeitskopien nicht erneut und beweist keine zeitlich unbegrenzte Frische nach dem damaligen Scan. Der historische Kurzbericht nennt noch den ursprünglichen Dateinamen `seed-audit.json`; die heutige verbindliche Archivlage ist über die oben geprüfte Root-Abnahme und das Rohgzip eindeutig.
- Task 3/4 einschließlich Runner/Supervisor, technische Vier-Spiel-Ausführung, tatsächliche Input-/Befehls-/Gewichtsbindung, Quellenfreeze, Ressourcen-/Prozesszulassung und spätere Paar-Vorlauf-/Enddatenabnahmen sind weiterhin separat erforderlich. Der parallel entstehende Task-3-Code war ausdrücklich kein Prüfgegenstand.
- V14 und ZIP wurden in diesem Audit weder geladen noch neu gehasht oder geändert. Keine Startfreigabe, technische Integrationsbehauptung, Stärkeaussage oder Promotion folgt aus diesem PASS.
