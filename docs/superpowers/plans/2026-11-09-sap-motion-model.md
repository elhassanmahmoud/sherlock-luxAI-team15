# Neue Hypothese: öffentlich gelerntes Bewegungsmodell für SAP

Der abgeschlossene Vorhaltescreen erreichte Solution40/40, direkt aber nur18/40. Er wird nicht verlängert. Diese Folgeidee ersetzt die pauschale Richtungsfortschreibung durch eine kleine, ausschließlich aus öffentlichen Beobachtungen des aktuellen Spiels gelernte Bewegungsverteilung und berücksichtigt verlorene Nebentreffer. Die 36 V14-Netze und Abgabe bleiben gleich. Die Methode ist unbewiesen.

## Vorab festgelegter Prototyp

- Separate Eval-Unterklasse; standardmäßig aus, kein Training der Q-Netze, kein zweiter Core-Aufruf. Normale V14-Aktion zuerst, danach höchstens der kleinste geeignete Schützen-UID mit SAP-Offsetänderung. Sonstige produktive Buchhaltung wie beim geprüften Vorhalteprototyp.
- Fünf relative nächste Bewegungen nach einer beobachteten kardinalen Bewegung: vorwärts, rechts, rückwärts, links, stehen. Für Richtung `(dx,dy)` sind die Vektoren `(dx,dy)`, `(-dy,dx)`, `(-dx,-dy)`, `(dy,-dx)`, `(0,0)`.
- Eine gepoolte Zähltabelle pro gegnerischem Team und Spiel. Alle geeigneten sichtbaren Einheiten erfassen, unabhängig davon, ob auf sie geschossen wurde. Nur drei unmittelbar aufeinanderfolgende öffentliche Positionen derselben UID im selben Match/Spiegelungsrahmen; aktuelle und vorherige Energie endlich/nichtnegativ, die Energie vor der gelabelten Bewegung mindestens Bewegungskosten. Ausschließlich beobachtete Bewegungen mit Manhattanlänge0oder1 zählen. Sichtlücken, Sprünge und Matchreset erzeugen kein Label. UID-Wiederverwendung bleibt eine Beobachtungsgrenze, keine garantierte Identität behaupten.
- Matchwechsel löscht Positionshistorie, hält aber die im aktuellen Spiel gelernten Zähler. `new_game` löscht beides. Keine Daten anderer Partien und keine spätere Position zur aktuellen Aktionswahl.
- Dirichlet-Prior `(1,1,1,1,1)`; `p=(counts+1)/(N+5)`. Erst ab32 tatsächlich beobachteten Übergängen ist ein Eingriff möglich. Diese Wahl ist vor neuen Ergebnissen fest und wird nicht nachjustiert.
- Bisherige öffentliche SAP-Eignung und sicher genug geschätzter Streufaktor unter1 bleiben. Verglichen werden nur das originale Zentrum und das um den zuletzt beobachteten Schritt vorgehaltene Zentrum.
- Fokusziel: pro Bewegungsart erwartetes Treffergewicht am neuen minus am alten Zentrum; direkter Treffer1, benachbarter Treffer gleich geschätztem Streufaktor, sonst0. Bekannte Kartenränder und sichtbare Asteroiden verhindern die entsprechende Bewegung; für solche Fälle bleibt die Position gleich. Keine verborgene Karte oder gegnerische Aktion verwenden.
- Andere sichtbare, nichtnegative Gegner werden im Vergleich konservativ an ihrer aktuellen Position berücksichtigt. Das ist eine explizite Modellannahme, keine sichere Bewegungsvorhersage. So werden verlorene Nebentreffer nicht ignoriert.
- Für Fokus-Gewinnvektor `g`, Posteriorgesamtmasse `A=N+5` und feste Änderung der anderen Treffer `b`: `mean=b+p·g`, `variance=(p·g²-(p·g)²)/(A+1)`. Nur bei `mean-2*sqrt(max(variance,0)) > 0` verschieben. Der Unsicherheitsabzug ist eine heuristische Auswahlregel, kein kalibriertes95%-Intervall oder Stärkenachweis.
- Bei jeder fehlenden Voraussetzung exakt die originale V14-Aktion erhalten. Eigene Diagnosezähler und die verwendeten Modellgrößen protokollieren, keine Entscheidungsabhängigkeit vom späteren Spielergebnis.

## Begrenzte Umsetzung und Prüfung

Zunächst nur separaten Prototyp und gezielte synthetische Tests entwickeln. Bestehende Core-/Gewichtsdateien nicht ändern. Ein Implementierer, ein enger unabhängiger Review; keine Wiederholung abgeschlossener Gesamtaudits. Danach genau festgelegte bekannte Integrationsspiele und ein kleiner neuer Vergleich mit eigenen Karten, gleicher Config und vorher definierten Hürden. **Dieser technische Entwurf allein startet keine Spiele.** Laufwerkzeuge sollen vorhandene Spiel-/Score-/Prozesshelfer wiederverwenden, keine neue allgemeine Infrastruktur aufbauen.

Der Nutzer hat autonome Fortsetzung und Akkubetrieb freigegeben. Reale Quota, höchstens zwei Modellworker, keine parallelen Tests und Schutz der bisherigen Abgabe bleiben maßgeblich. Neue Rohdaten werden erst nach festem Vergleichsplan erzeugt; bei fehlendem Vorteil bleibt V14.

## Fester Folgeumfang vor neuen Ergebnissen

Die lokale Kartenprüfung läuft getrennt. Vorgesehen und vorab festgelegt sind ausschließlich Panel9942000–9942019 und Direkt9942100–9942119, jeweils beide Seiten. OFF und ON gegen Solution ergeben80Spiele, ON direkt gegenOFF weitere40. Beide Rollen erhalten dieselbe explizite V14-Config mit frozen=False/Eval/Epsilon0 und dieselben36Gewichte. OFF deaktiviert ausschließlich den neuenHook. Keine Wiederverwendung der vorigen Screenkarten und keine Erweiterung bis zu einem gewünschten Ergebnis.

Vor diesen120Spielen genau dieselben zwei bekannten technischen Schlüssel mit beiden Modi: OFF831006/player_1, OFF831000/player_0, danachONaufbeiden. OFF muss wieder alle303nativenBefehle und gespeichertenAktionshash-/Match-/Version2-Punktedaten reproduzieren. ON muss insgesamt mindestens einen echtenEingriff mit korrekt ausöffentlichenDaten rekonstruiertenZählern/Posterior/Unsicherheitsabzug haben; ansonsten keinErsatzspiel. WeitereAktionen undBuchhaltung bleiben erhalten. Maximalvier bekannteAusführungen, getrenntvonLeistung.

Alle drei vorab festgelegten Screenhürden gelten unverändert: EingriffeaufmindestensfünfPanelkarten, Solution-ScoreON≥OFF, direktmindestens60Prozent (`2W+D>=48` bei40Spielen). ScoreausMatchsiegen, Remishalb. GanzeKarten einschließlichbeiderSeiten/gepaartenRollen gemeinsamresamplen,5000ZiehungenPCG64Seed0; Intervalledeskriptiv. EinFehlschlag schließt diesenVersuch ohneNachschlag. EinErfolg erlaubt nurseparateBestätigung, keineautomatischeÜbernahme. KeineStärkeausdenbekanntenTechnikkartenableiten.

TatsächlicherStart erst nach aufgenommenenWerkzeugen, realemfrischemKontingent undgehashterRoot-Aufnahme. Code/HEADbleiben imLauffest. DieStromausnahme istbereitsvomNutzerautorisiert; keineweitereNetzteilfrage.

## Tatsächlicher Abschluss am 09.11.

124 Ausführungen vollständig; Solution beide 38/40, direkt 21/40. Direktgate verfehlt, kein Nachschlag oder Ersatz für V14. Originalanalyse und unabhängige Datenchecks bestanden, V14/ZIP unverändert. [Ergebnis](../../../experiments/analysis/sap_motion_screen_20261109/ERGEBNIS.md). Neue Aggregation ist eine separate Hypothese.
