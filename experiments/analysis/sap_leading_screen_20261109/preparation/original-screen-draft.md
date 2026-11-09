# Entwurf: einmaliger SAP-Vorhalte-Screen

**Status:** reine Planung, keine Startfreigabe. Der technisch aufgenommene Prototyp besitzt 44 synthetische Tests und unabhängigen statischen Review; tatsächliche Modell-/Spielintegration ist noch offen. V14 bleibt Abgabe. Ein positiver Screen erlaubt ausschließlich einen getrennten Folgeentwurf, keine Übernahme.

## Feste Rollen und Matrix

Beide Rollen verwenden dieselben 36 V14-Netze, dieselbe gebundene Checkpointconfig und dieselben Ladewege: explizit `frozen=False`, Eval/epsilon0, `autosave_on_terminate=False`, kein Update. Kontrollrolle ist die Unterklasse mit `lead_enabled=False`, Lead dieselbe Klasse mit `True`; damit einziger Entscheidungsunterschied der bereits geprüfte Hook. Original-V14-Passivität wird vorab technisch geprüft. Auch beide Direktduellseiten erhalten explizit dieselbe normalisierte Config; keine implizite Self-Play-Standardconfig.

| Block | Vorgeschlagene Karten | Rollen/Seiten | Spiele |
|---|---|---|---:|
| Solution92 | 9940000–9940019 | V14 und Lead jeweils beide Seiten | 80 |
| Direkt | 9940100–9940119 | Lead gegen V14, beide Seiten | 40 |

Exakt120 Leistungsspiele, 20 gemeinsame Panelkarten und 20 getrennte Direktkarten. Bereiche sind **nur Vorschläge**; Root prüft Frische/Reservierungen separat vor Fixierung. Aufsteigende Kartenfolge, jeweils Seiten0/1; feste Rollenreihenfolge V14,Lead. Kein Zwischencheckpoint, kein Ensemblewechsel. Lead behält stets sämtliche festen öffentlichen Filter, Parameterposterior≥0,9 bei Faktor<1 und maximal einen Eingriff auf der kleinsten geeigneten UID je Schritt. Keine nachträgliche Änderung von Schwellen, Quoten, Karten oder Gegnern.

## Minimale technische Aufnahme: höchstens vier bekannte Spiele

Vor Leistungsdaten einmal OFF auf `831006/player_1` und `831000/player_0`, anschließend ON auf genau denselben Schlüsseln; keine frischen Karten hierfür. OFF muss jeweils alle303 eigenen nativen Aktionsarrays, den gemeinsamen Aktionsstreamhash und v2-Punkte/Matchsiege gegen die gebundenen historischen Targeting-Belege reproduzieren. Beide Gewichtsdateien bleiben SHA`98a07350…d3d8`; vollständige Hashes, Config,36 Mitglieder und Quellen vorher festhalten.

ON prüft tatsächliche Eingriffe ohne Stärkeauswertung: passiver Mitschnitt vor/nach dem Hook, genau ein originaler `_act`-Aufruf, unveränderte anderen Zeilen/Aktionsklasse, korrekte native Spiegelung, öffentliche Eligibility samt aktualisiertem Posterior, kleinstmögliche UID, Buchhaltungsdelta und nachfolgendes `param_est._prev['act']` gleich eingereichtem Befehl. Kein zusätzlicher Entscheidungs-/Observe-/Remember-Aufruf. Zähler/Reset und Null-Eingriffsschritte ebenfalls prüfen. Mindestens ein realer Eingriff über beide ON-Spiele muss vorkommen; andernfalls bleibt der aktive Integrationsnachweis offen und die Technik schließt ohne Ersatzspiel. Jede Abweichung stoppt; kein automatischer Wiederholungsstart. Diese maximal vier Ausführungen sind separat von120 zu berichten.

## Erfassung und feste Entscheidung

Kleiner Runner um vorhandenes `common.play_game(...,train=False)`, vorhandene Punkte-/Bootstraphelfer; kein neuer Supervisor. Drei feste Ergebnisdateien, eindeutige Spielschlüssel,303 Schritte, keine abgefangenen Agentfehler. Pro Spiel Roh-W/D/L, Matchsiege/Punkte, Lead-Ausschlüsse, geeignete SAPs und tatsächliche Änderungen sichern; Quellen-/Inputhashes und unveränderte Schutzdateien binden. `common.play_game` übernimmt eigene Lead-Zähler nicht automatisch: Runner kopiert sie nach jedem Spiel zusätzlich, bevor `new_game` zurücksetzt.

Alle drei Weiterbedingungen müssen gelten:

1. Tatsächliche Lead-Interventionen auf mindestens fünf verschiedenen **Panelkarten**; eine Seite genügt zur Kartenexposition.
2. Solution-Score Lead≥V14 auf denselben40 Spielen.
3. Direkt-Score Lead≥60%: `2W+D≥48` bei40 Spielen.

Score bedeutet `(W+0,5D)/N`, Spielausgang nach Matchsiegen, nicht Gesamtpunkten. W/D/L und Scoreunterschiede vollständig berichten. 95%-Intervalle: bestehender 5000facher Whole-map-Bootstrap/PCG64-Seed0, beide Seiten und gepaarte Panelrollen gemeinsam resamplen. Nur20 Kartencluster je Block; Intervalle und Exposition sind deskriptiv, keine zusätzlichen nachträglichen Gates. Jeder Gatefehlschlag schließt ohne Nachschlag; technische Unvollständigkeit ist ebenfalls kein positives Ergebnis. Keine automatisierte Bestätigung oder Promotion.
