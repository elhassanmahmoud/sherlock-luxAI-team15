# Tatsächliche Motion-Technikdaten: unabhängiger enger Check

**PASS, kein Datenblocker.** 09.11.2026. Rein lesende Nachrechnung der abgeschlossenen Technikphase unter Quelle `4ceff1943e274f476dab82c37b9a93e682a00c63`: Exit 0, **16.462 erfolgreiche Prüfungen**. Vorhandener enger Leading-Datenprüfer außerhalb des Repositories auf das neue Ereignisformat und Bewegungsmodell angepasst; ausschließlich Standardbibliothek, keine Projekt-/Torchimporte, Tests, Modelle, Forwards oder Spielwiederholung. Die laufenden 120 Performancepartien wurden nicht gelesen oder beeinflusst.

| Modus | Karte/Seite | Frames | SAP-Offsetwechsel | Rekonstruierte Bewegungszähler am Ende |
|---|---|---:|---:|---|
| OFF | 831006/player_1 | 303 | 0 | 0/0/0/0/0 |
| OFF | 831000/player_0 | 303 | 0 | 0/0/0/0/0 |
| ON | 831006/player_1 | 303 | 18 | 31/13/0/10/5, insgesamt 59 |
| ON | 831000/player_0 | 303 | 0 | 24/10/1/4/6, insgesamt 45 |

Zählerreihenfolge: vorwärts/rechts/rückwärts/links/stehen. Beide OFF-Spiele stimmen in **allen 303 eigenen nativen Aktionsarrays**, gespeichertem gemeinsamem Aktionshash, vollständigen Matchdaten, Matchsiegen und v2-Punktesummen exakt mit ihren historischen Targeting-Belegen überein.

Alle 1.212 Frames wurden auf Reihenfolge, eindeutige öffentliche Gegner-IDs, Vorgeschichtsverknüpfung und Matchreset geprüft. Für ON wurden die Labelzähler aus den drei unmittelbar aufeinanderfolgenden gespeicherten öffentlichen Beobachtungen unabhängig neu aufgebaut, einschließlich Energie-/Bewegungsbedingungen, relativer Klasse und Resetgrenzen. Keine spätere Position wurde für die Entscheidung des aktuellen Frames verwendet. Die so berechneten Zähler stimmen **in jedem Frame** mit dem Protokoll überein; OFF sammelt keine Labels.

Öffentliche SAP-Eignung, Parameterposterior, Kandidatenmenge und kleinste geeignete UID wurden nachgerechnet. Für alle zulässigen Kandidaten wurden nächste Klassenpositionen, sichtbare Hindernisse/Ränder, Fokusgewinn, Änderung anderer sichtbarer Treffer, Dirichletwahrscheinlichkeiten, Mittelwert, Varianz und heuristischer Unsicherheitsabzug rekonstruiert. Gespeicherte Kandidaten- und Entscheidungsdiagnosen stimmen bis auf numerische Toleranz `1e-11` überein. Erster tatsächlicher Eingriff nach 37 Labels; kleinster positiver Auswahlwert unter den 18 Eingriffen **0,008612170532583813**, kleinste Dropoff-Konfidenz **0,9999942870558913**.

Je Frame höchstens eine geänderte SAP-Offsetzeile, keine andere Aktionsklasse oder andere Befehlszeile verändert. Native Spiegelung sowie genaue Hit-/`sap_hits_est`-/Unknown-Anpassung geprüft; übrige gespeicherte Buchhaltung, Pendingdaten, Features und Masken identisch. Die gesamten Änderungs-, Eligibility-, SAP-, Label- und Reset-Summen passen. Auch sämtliche Null-Eingriffsschritte wurden geprüft.

Abgeschlossener Owner-State (Exit 0, `active=[]`), genaue vier Rohzeilen, tatsächlicher Workerbefehl, Aufnahme-/Receiptkette und identische Quellen-/Configobjekte geprüft. Alle fünf Rohdateihashes sowie gebundene Inputs/Schutzdateibytes stimmen. Kein umfassender erneuter Quelleninventar- oder Codereview; der Technikstate war vor und nach der Nachrechnung bytegleich.

Maschinenlesbarer Bericht mit konkreten Eingangshashes und allen Eingriffssteps: `/tmp/sap-motion-technical-review.json`, SHA-256 **`4282de55de23475cd93606804622b15e6b44712b8d4fea9a46588893f0fd3f4d`**. Aufnahme SHA `4f8cd240b1fe8b8070c4521f4f6f01798186eb3108e08c1e51e6e62d6f9e2b50`; Receipt SHA `f056852a7d5a9791b82ba20acea83b7f54d0960038a9fbb4ab56111f3af8110e`. Eigenständiger enger Nachrechner: `/tmp/sap-motion-technical-check.py`.

Grenzen: Kombinierter Aktionshash gegen den historischen Wert verglichen; gegnerische native Roharrays sind nicht separat archiviert, deshalb kein unabhängiger Neuaufbau dieses gemeinsamen Hashes. Original-Remembergleichheit und genau ein Core-Aufruf sind erfolgreiche Liveassertionen des gebundenen Workers; ihre Werte liegen nicht gesondert zur nachträglichen Messung vor. Öffentliche Beobachtungen werden als protokollierte Laufdaten verwendet, ohne Engine-Replay oder Identitätsgarantie bei UID-Wiederverwendung. Der Unsicherheitsabzug ist nicht kalibriert. Bekannte technische Karten belegen weder allgemeine Stärke noch kausalen Vorteil oder Promotion; Leistungsdaten sind nicht Gegenstand dieses Checks.
