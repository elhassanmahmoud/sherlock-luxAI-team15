# Enger statischer Review der Akkuoption

**PASS, keine blockierenden Findings.** 09.11.2026. Geprüft wurde ausschließlich der konkrete Vier-Dateien-Diff gegen HEAD `0fff2e97302c2e11c2aef67cb1c53cf037067fc9`; kein erneuter Gesamt-Codereview, kein eigener Test-/Modell-/Spielstart.

- `fog_reward_supervisor.guard(..., *, allow_battery=False)` behält den bisherigen Default bei und akzeptiert ausschließlich echte Boolwerte. Bei `True` entfällt genau die AC-Pflicht. `read_power` und die Aufzeichnung des tatsächlichen Stromzustands bleiben erhalten; keine neue Akkuuntergrenze oder sonstige Stromauflage wurde eingeführt. Die Akkuüberwachung liegt gemäß Nutzerfreigabe beim Nutzer.
- STOP, tatsächliche Quota samt Frische, Quellen-/HEAD-/Planidentität, sämtliche Input-/Gewichts-/ZIP-Hashes und Prozessprüfung sind unverändert. Die Option umgeht keine dieser Prüfungen. Bestehende andere Aufrufer ohne Keyword behalten ihre bisherige Semantik.
- Die SAP-Aufnahme verlangt einen booleschen `allow_battery`-Wert innerhalb der per CLI-SHA gebundenen JSON. Der Owner kopiert genau diesen Wert in seinen State und übergibt ihn an alle vier Guard-Aufrufstellen. Der Worker verlangt einen echten Boolwert im State und exakte Gleichheit mit der Aufnahme; erst danach übergibt er den Aufnahmewert an den Guard. Aufnahmehash und Inputbindung bleiben zusätzlich erhalten.
- Auch die spätere Analyse bindet den geschlossenen State an denselben Boolwert. Der neue Wert ändert weder Technik-/Performancegrenzen noch Spielmatrix, Reihenfolge, Wiederholungsschutz oder Ergebnisregeln.
- Die Ergänzungen der synthetischen Tests decken DefaultFalse, ausdrückliches True, Ablehnung boolähnlicher Werte, Fortbestand der übrigen Schutzprüfungen und Owner-/Workerbindung ab. Implementierer meldet 50 Tests PASS in 2,40s; dieser Reviewer hat sie ausschließlich gelesen und nicht erneut ausgeführt.

| Geprüfte Datei | SHA-256 |
|---|---|
| `scripts/fog_reward_supervisor.py` | `84a04f5c9b542c676211b6b28eefbe74f3fcc280d36e1a1580281766e0b70073` |
| `scripts/sap_leading_eval.py` | `bb92fa880a8adcaaf05f02bdf08a5fc3c689a8df8387077749dd7974b4f1acca` |
| `scripts/sap_leading_owner.py` | `5cfdc4b0f25f34a7a9823cf7b5f1a69bfcb8e75c56b6f4ae7488901fd73319d0` |
| `tests/test_sap_leading_screen.py` | `29148c10e3852e3a946623e92b4604e25a2a036233919716ba044aea5cb036b8` |

Die alte Aufnahme mit SHA `add57e45…f6b1e` enthält noch keinen Akkuwert und bindet die vorherigen Quellbytes; sie bleibt ein historischer Beleg. Für den vorgesehenen Akkulauf ist entsprechend dem geprüften Vertrag die aktualisierte gehashte Root-Aufnahme mit `allow_battery=true` und aktuellem Quellenstand maßgeblich. Kein zusätzlicher AC-Vorbehalt aus diesem Review. Reale Integration bleibt bis zu den tatsächlichen vier Technikdaten offen; keine Stärkeaussage.
