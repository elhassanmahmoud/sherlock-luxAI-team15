# Enger unabhängiger Review: SAP-Bewegungsmodell und Runner-Diff

**PASS im statischen Umfang, keine blockierenden Findings.** 09.11.2026. Neuer Agent und gesamte neue Agenttestdatei gegen den festen Plan gelesen; anschließend vollständiger Motion-Runner-/Owner-Diff zur bereits geprüften Leading-Version und gesamte neue Runnertestdatei. Keine eigenen Tests, Projektimporte, Modelle, Forwards oder Spiele. Kein erneuter Gesamtaudit des unveränderten alten Codes und keine Repoänderung.

## Konkreter Methodenabgleich

- `_observe_motion` verwendet ausschließlich kopierte öffentliche Positionen/IDs/Energien aus drei aufeinanderfolgenden Beobachtungen. Gelabelt wird bei aktueller Beobachtung t der bereits abgeschlossene Schritt t−1→t relativ zur Richtung t−2→t−1; diese Zähler dürfen anschließend die Entscheidung für t→t+1 beeinflussen. Keine zukünftige Position, fremde Aktion oder Enginewahrheit fließt ein. Alle geeigneten sichtbaren Gegner werden gepoolt, unabhängig von einem SAP.
- Schritt-, Match- und Spiegelungskontinuität sind erforderlich; dieselbe UID muss in allen drei Beobachtungen sichtbar sein. Vorige Richtung Manhattan 1; gelabelter Schritt Manhattan 0 oder 1; beide letzten Energien endlich/nichtnegativ und vorige Energie mindestens Bewegungskosten. Relative Klassen stimmen mit dem Plan überein: vorwärts, `(-dy,dx)`, rückwärts, `(dy,-dx)`, stehen. Sichtlücken/Sprünge erzeugen kein Label. Eine lückenlos sichtbare wiederverwendete UID bleibt wie geplant eine Beobachtungsgrenze.
- Matchreset und ungültiger/unterbrochener Kontext löschen Positionshistorie, nicht die innerhalb des Spiels erworbenen Zähler. `new_game` verwendet den tatsächlichen virtuellen Resetpfad und löscht Historie, Zähler und eigene Diagnosen. OFF ruft nur den originalen Core auf und verändert keinen produktiven Aktions-/Buchhaltungszustand; keine Modelllabels werden gesammelt.
- `p=(counts+1)/(N+5)`, Mindestmenge 32 abgeschlossene Labels, geometrischer Gewinnvektor und additive Änderung anderer sichtbarer nichtnegativer Gegner passen. Rand und aktuell sichtbares unpassierbares Feld führen zur angenommenen Standposition; unbekannte Felder werden ausdrücklich nicht als bekannte Hindernisse verwendet. Varianz `(p·g²−(p·g)²)/(N+6)`, Nullbegrenzung und striktes `mean−2√variance>0` entsprechen dem Plan. Der Abzug bleibt eine Heuristik, kein kalibriertes Konfidenzintervall. Die Stationarität anderer Gegner ist eine explizite Annahme.
- Genau ein `Agent_x._act` umgeht gezielt den unbedingten Hook der Elternklasse. Das originale `_act_est` beobachtet davor und merkt danach den finalen nativen Befehl. Die bestehenden öffentlichen SAP-Filter und sichere Dropoff-Schätzung bleiben; nach allen Zusatzgates wird nur die kleinste geeignete Schützen-UID verändert. Nur deren Offset wechselt, die Klasse bleibt SAP. Native Spiegelung, sichtbare 3×3-Hitbuchhaltung, statistisches Delta und Unknown-Entfernung entsprechen der geprüften Leading-Variante; andere Befehle/Pendingdaten bleiben unverändert. Keine zweite Entscheidung oder zweiter Forward.

## Enger Runnerabgleich

Neue Factory lädt tatsächlich `SapMotionAgent` für beide Rollen mit derselben expliziten V14-Config; neuer Profil-/Ausgaberaum und genau Panel9942000–9942019 sowie Direkt9942100–9942119. Technikschlüssel und Reihenfolge bleiben die vier festgelegten bekannten Ausführungen. Die neue Beobachterhülle rekonstruiert alle fünf Labelzähler, Posterior, Geometrie, Unsicherheitsabzug, kleinste UID und finale native Aktion unabhängig von den Agentenhelfern. Sie vergleicht tatsächliche Modellzähler/Diagnosen und archiviert vorherige Historie, Zähler sowie Entscheidung. Match-/Spiegelungsunterbrechungen und abgeschalteter Hook sind im Auditpfad konsistent behandelt.

Der Owner-Diff besteht ausschließlich aus dem neuen Worker-Modulnamen. Aufnahme-/Quellen-/Gewichts-/Quota-/STOP-/Prozessbindung, ausdrücklich erlaubter Akkubetrieb, maximal zwei Worker, exklusive Ausgaben und kein Retry/Phasenautomatismus bleiben unverändert. Die 120er-Matrix, drei Gates und Ganzkartenstatistik wurden übernommen; keine neuen nachträglichen Hürden oder Kartenänderung im Diff.

## Tatsächliche Prüfevidenz

Gelesenes `/tmp/sap-motion-impl/final-tests.log`: **70 PASS in 2,37s**, ausdrücklich **26 neue Motion- plus 44 bestehende Leading-Fälle gemeinsam**. Implementierer bestätigt den Aufruf mit der Projekt-venv, `python -B -m pytest -q -p no:cacheprovider tests/test_sap_motion_agent.py tests/test_sap_leading_agent.py`, Bytecode aus und vier numerische Threadvariablen auf 1. Die gemeinsame Fixture sperrt QNet und `torch.load`, ersetzt Konstruktor/Core und verwendet den echten `_act_est`-/Rememberpfad. Kein echter Netz-/Engineintegrationstest.

Gelesenes `/tmp/sap-motion-runner/GREEN.log`: **30 neue synthetische Runnertests PASS in 0,24s**, gleicher Interpreter/Umgebung, ausschließlich `tests/test_sap_motion_screen.py`. Keine eigenen Wiederholungen durch diesen Reviewer. Diese Tests prüfen den geänderten Vertrag; sie sind keine reale historische Reproduktion. Die vier tatsächlichen Technikspiele, ON-Exposition und späteren Leistungsdaten bleiben offen.

| Geprüfte Datei/Beleg | SHA-256 |
|---|---|
| `scripts/sap_motion_agent.py` | `1bfa0e34ba60545a7e6806360da6c1d520eb80c2ad4bea6ccb5a74f028b00900` |
| `tests/test_sap_motion_agent.py` | `4bb1fdfcbc4f2b9527662cb921b164b598cb6e66e70627afff44163df55aabc6` |
| `scripts/sap_motion_eval.py` | `10485a00a24b571ec03eacfa0c9f6725771f25592267d6dc315be5f657fbcb59` |
| `scripts/sap_motion_owner.py` | `ef7432694b1f8e2de8842a0c1b640af3c84e1ab1bc8355232981f6ea5ca80e53` |
| `tests/test_sap_motion_screen.py` | `97c414462fcee1f8f67b5f762cf2639b6cf396566f699f61e62f6b2a861da2de` |
| Plan `docs/superpowers/plans/2026-11-09-sap-motion-model.md` | `bc199fc94c400d1dfe7bc1487ca7a2f8f5ed35c9f0eb0ef07870b79c7a987d99` |
| `/tmp/sap-motion-impl/final-tests.log` | `cb2967d58d4ab604ca38894113040f67722a107dbc682c9d879e9894baa5c7c9` |
| `/tmp/sap-motion-runner/GREEN.log` | `dd662b76eb38c0d930f3da911be9db6b3ab567f86b724a38c302e03008d82b7d` |

Dieser statische PASS ist keine Spielstartfreigabe und keine Stärkeaussage. Die separate Root-Aufnahme und tatsächliche technische Prüfung bleiben maßgeblich; V14/ZIP werden durch diesen Review nicht verändert.
