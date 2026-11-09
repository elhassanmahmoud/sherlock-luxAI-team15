# SAP-Vorhalten: technischer Nachweis und kleiner Vergleich

**Noch keine neuen Spiele, kein Training und kein Stärkenachweis.** V14 und die bestehende ZIP bleiben unverändert. Diese Vorbereitung ergänzt den getrennten Prototyp; sie wiederholt keine abgeschlossene Studie.

Der [feste Plan](../../../docs/superpowers/plans/2026-11-09-sap-leading-screen.md) sieht zuerst höchstens vier bekannte Technikspiele vor. Nur nach erfolgreicher Abnahme folgen 120 Leistungsspiele: OFF und ON jeweils 40 gegen Solution_92 sowie 40 direkte ON-gegen-OFF-Spiele. Beide Rollen haben dieselben 36 V14-Netze. Die einzige Verhaltensänderung ist höchstens ein öffentlich begründeter SAP-Offsetwechsel pro Schritt.

## Bisher tatsächlich geprüft

- Der bereits aufgenommene Agentenprototyp besitzt seinen separaten [44-Test-Nachweis](../sap_leading_prototype_20261109/README.md); diese Tests wurden hier nicht nochmals gezählt oder wiederholt.
- Der neue Runner wurde vom Implementierer synthetisch geprüft. Nach bytegleicher Aufnahme ins Repo hat Root die neue Testdatei ausgeführt: **37 Tests bestanden in 2,38 Sekunden**. QNet-Konstruktion und `torch.load` sind in diesen Tests gesperrt. [Exakter Root-Prüfbeleg](preparation/ROOT_INTEGRATION.json), ursprüngliche RED/GREEN-Logs im selben Ordner.
- Der schmale Root-Launcher nutzt vorhandene Start-, Schutz- und Aufräumhelfer. Er ist syntaktisch geprüft, aber noch nicht tatsächlich ausgeführt. Er startet nur eine ausdrücklich aufgenommene Phase; weder automatischer Phasenübergang noch Wiederholungsstart.
- Vollständiger unabhängiger statischer [Review von Runner, Tests und Launcher](preparation/INDEPENDENT_REVIEW.md): keine blockierenden Befunde. Echte Engineintegration und aktiver Eingriff bleiben durch die vier bekannten Technikspiele nachzuweisen.
- [Begrenzter lokaler Kartencheck](preparation/seed-review.md): keine beobachtete Nutzung oder ältere Reservierung der beiden festen Bereiche in acht Arbeitskopien. Der ursprüngliche `REVIEW_REQUIRED`-Befund wegen des damaligen primären Git-Updates bleibt erhalten; dessen konkreter Delta wurde separat geprüft. [Root-Annahme mit Grenzen](preparation/seed-acceptance.json).

Der vollständige ursprüngliche Kartenbericht ist verlustfrei in `preparation/seed-audit.json.gz` gespeichert; sein dekomprimierter SHA-256 ist `2c800a2fcb7b4d42638b916ceee8dc5e8c164abd301439c609fa1ad7814aaff8`. Seedlose, ausschließlich in Roh-JSONL dokumentierte und externe Historie ist damit nicht ausgeschlossen. Die ursprünglichen Reviews enthalten historische `/tmp`-Pfade; ihre Belegbytes liegen jetzt im selben Vorbereitungsordner.

## Vor einem echten Lauf

Aktuellen Arbeitsstand und tatsächliche Prozesse prüfen. Der Runner `scripts/sap_leading_eval.py` benötigt eine getrennte, gehashte Root-Aufnahme pro Phase; `scripts/sap_leading_owner.py` startet die festen Worker mit maximal zwei gleichzeitig. Quelle, Launcher und Eingaben binden und echte frische Quota prüfen. **Moayeds ausdrückliche Freigabe vom 09.11. erlaubt Akkubetrieb für diesen Vergleich:** `allow_battery=true` in der gehashten Aufnahme und im gebundenen Owner-State; ohne diese Ausnahme bleibt Netzstrom erforderlich. Der [ursprüngliche Aufnahmevertrag](preparation/IMPLEMENTATION.md) bleibt als historischer Beleg erhalten; beim Aufruf den aufgenommenen Repo-Launcher statt des dort dokumentierten ursprünglichen `/tmp`-Pfads verwenden.

Technik und Leistung schreiben ausschließlich in neue `technical_v1` beziehungsweise `performance_v1`-Verzeichnisse. Existierende Ausgaben und Startreservierungen niemals löschen, überschreiben oder als Wiederholungsfreigabe behandeln. Die Quellen bleiben während der Läufe fest. Tests vorher abschließen; keine Tests parallel zu Modellläufen.

Ein positiver 120-Spiel-Screen wäre nur ein Hinweis für einen getrennten nächsten Entwurf. Er ist weder eine allgemeine 100-Prozent-Quote noch eine Übernahmefreigabe.
