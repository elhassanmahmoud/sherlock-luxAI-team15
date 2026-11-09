# SAP-Vorhalteprototyp – technische Aufnahme

09.11.2026. Der separate Prototyp ist aufgenommen und synthetisch geprüft. **Noch keine tatsächliche Netz-/Spielintegration und keine Stärkeaussage.** V14 und die ZIP bleiben unverändert; die produktiven Agentendateien wurden nicht geändert.

Die neue Klasse `scripts.sap_leading_agent.SapLeadingAgent` ist standardmäßig deaktiviert (`lead_enabled=False`), ausschließlich für Evaluation und verweigert Training/Updates. Im aktivierten Modus darf sie pro Schritt höchstens einen schon bestehenden SAP auf die öffentlich vorausgesagte nächste Gegnerposition verschieben. Alle36 bestehenden Netze und die originale Aktionsentscheidung bleiben erhalten. Nur bei ausreichender öffentlicher Historie, legalem Ziel und vorhandener Streuschadenschätzung mit mindestens0,9Konfidenz und Faktor<1 darf der kleinste geeignete Schützen-UID geändert werden.

Das Original beobachtet Parameter vor dem Hook und erinnert danach den tatsächlich gesendeten Befehl. Zielabhängige Trefferbuchhaltung wird als Differenz korrigiert; SAP-Anzahl, andere Befehle, Aktionsklasse und Pendinglisten bleiben erhalten. Siehe [Buchhaltungsreview](bookkeeping-review.md) und [unabhängigen Prototypreview](INDEPENDENT_REVIEW.md).

## Tatsächliche Prüfungen

- Implementierer: zunächst zwei gezielte RED-Fälle, zuletzt44synthetische Tests PASS1,55s. Zwischenfehler der numerischen Testfixture sind im [Implementierungsbericht](IMPLEMENTATION.md) erklärt; Schwellenwert und Originalschätzer unverändert.
- Root: gesamte Implementierung/Testdatei/Reviews gelesen, Agent-/Testdateien bytegleich übernommen; danach44Repo-Tests PASS2,57s zur Prüfung des geänderten Importorts. [Rohlog](ROOT_INTEGRATION.log), [Datei- und Prüfnachweise](admission.json).
- Die synthetischen Tests sperren echte Netz-/Gewichtskonstruktion. Das sind keine vollständigen Spiele und kein36-Netz-Laufnachweis.
- Gewichte beider Seiten weiterhin SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

## Offen

Vor tatsächlichen Läufen benötigt der Prototyp den separat festgelegten technischen Nachweis und einen kleinen festen Vergleich mit ungenutzten Karten. Ein120-Spiele-Screen gegen Solution/V14 wird vorbereitet; er ist noch nicht durchgeführt und würde allein keine Abgabefreigabe liefern. Keine geschlossenen Studien wiederholen oder Rohdaten als neue Ergebnisse ausgeben.
