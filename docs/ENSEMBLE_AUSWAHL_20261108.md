# Neue Ensemble-Netze: kompakte Auswahl vom 08.11.2026

**Positive Hinweise, aber kein nominierter V14-Nachfolger. V14 bleibt unverändert.**

Alle 39 Jobs und 1560 Spiele sind vollständig. Die unabhängige Prüfung hat Rohdaten, Karten/Seiten, Ausführung, Modelle/Quellen und alle Berechnungen bestätigt. Es gibt keine fehlenden, doppelten oder ausgeschlossenen Ergebniszeilen. Gemessen wurde auf 20 Karten für Gegnervergleiche und 20 separaten Direktkarten, jeweils beide Seiten. Alle Werte sind explorative Auswahlergebnisse.

| Variante | Netze | Siege im Sechserpanel | Solution | default | Direkt gegen V14 |
|---|---:|---:|---:|---:|---:|
| V14 |36|185/240|38/40|40/40|–|
| A39 |39|202/240|39/40|40/40|18/40|
| B39 |39|193/240|39/40|40/40|14/40|
| ALL42 |42|205/240|40/40|40/40|18/40|
| REPLACE36, nur Diagnose |36|202/240|39/40|40/40|28/40|

Keine Remis in diesen Daten. Das Sechserpanel umfasst Solution_92, sol92_sq und die festen V3/V7/V10/V13-Gegner; default wird getrennt berichtet. Dieses lokale Panel ist nicht Mahmouds historisches Battle-Panel.

ALL42 erreicht im Panel +8,33 Prozentpunkte gegenüber V14, exploratives 95%-Kartenintervall [+1,25;+14,58]. Gegen Solution sind es 40/40 statt 38/40; das Differenzintervall [0;+15] Prozentpunkte schließt Null ein. Das belegt keine allgemeine 100%-Siegquote. Direkt erreicht ALL42 nur 45 % auf 40 Spielen, Intervall [25;65,0625]%. Alle drei nominierbaren Erweiterungen verfehlen die vorab festgelegte direkte Punktschätzungsgrenze von 50 %. Daher bleibt `nominee:null`; es wird keine Bestätigung in diesem kompakten Protokoll gestartet.

Die diagnostische Austauschvariante REPLACE36 entfernt die sechs vorab bestimmten älteren Mitglieder [0,6,12,18,24,30] und setzt die sechs neu trainierten ein. Sie erreicht im Panel +7,08 Prozentpunkte[+0,83;+13,33] und direkt 70 %[50;90]%. Sie war ausdrücklich nicht nominierbar und wird nachträglich nicht umetikettiert. Schon die untere direkte Intervallgrenze liegt nicht über 50 %, wie es eine Bestätigung verlangen würde. Ein allgemeiner Vorteil von weniger Netzen oder ein bestimmter Wirkmechanismus ist dadurch nicht gezeigt; Anzahl, Zusammensetzung und Gewichtung verändern sich gemeinsam.

## Vorgehen und Grenzen

Auf Nutzerwunsch wurde der Umfang vor Ergebnisprüfung reduziert. Der zuvor kurz gestartete große Auswahlversuch endete kontrolliert ohne gespeicherte Ergebnis-CSV; seine tatsächlich intern berechnete Spielzahl ist unbekannt. Beide alten Kartenblöcke bleiben ausgeschlossen und alle Betriebsbelege erhalten. Die 1560 vollständig dokumentierten kompakten Spiele dürfen damit nicht als exakte Gesamtzahl aller seitdem ausgeführten Partien bezeichnet werden.

Die sechs neuen Netze wurden davor bereits vollständig trainiert und geprüft: 18.000 Lernspiele plus Vorlauf/Validierung, 2,7 Mio. Updates. Diese Lern- und bekannten Validierungsdaten sind getrennt vom frischen Vergleich. [Trainingsbericht](ENSEMBLE_TRAINING_20261107.md).

Die Auswertung nutzt unveränderte ursprüngliche Ensemble-Gates, gepaarten Bootstrap ganzer Karten mit beiden Seiten, 5000 Ziehungen/PCG64 Seed0. Nur 20 unabhängige Karten je Auswahlblock und mehrere untersuchte Varianten: nominale 95%-Intervalle sind explorativ und keine über alle Studien korrigierte Garantie. Keine zusätzlichen Karten bis Signifikanz, keine alten Daten beigemischt.

## Separater nächster Ansatz

Die kompakte Studie endet ohne Nomination und ohne Bestätigung. Unter dem breiteren autonomen Verbesserungsauftrag empfiehlt der [unabhängige Methodenreview](../experiments/analysis/ensemble_diversity_20261108_compact/next_step_review.md) einen einmaligen, getrennt vorab festgelegten Frischdatentest genau des bestehenden REPLACE36-Modells. Das ist ausdrücklich durch das diagnostische Ergebnis motivierte Folgeforschung, keine erfolgreiche Nomination im kompakten Protokoll.

Dieser Folgetest erhält maximal 3200 Spiele, keinen weiteren Nachrücker oder Nachschlag, dieselben Übernahmegates und keine Änderung der Netze/Regeln. Gesamtumfang beider vollständiger Phasen maximal 4760 Spiele, zusätzlich unbekannte Ausführungen des gestoppten Großstarts. Noch nicht gestartet; eigene Planung, Werkzeugprüfung, frische Karten und Source-Freeze sind erforderlich. Neue Daten allein entscheiden. Bei negativem/unklarem Ausgang bleibt V14 und es gibt keinen automatischen weiteren Versuch.

[Rohdaten und Zusammenfassung](../experiments/analysis/ensemble_diversity_20261108_compact/selection/) · [unabhängiger Datenaudit](../experiments/analysis/ensemble_diversity_20261108_compact/selection/independent_audit.md).

V14 und abgegebene ZIP sind bytegleich; keine Moodle-Abgabe verändert. Quelle der Messung 2146494ee12ce288b48ae69bde119198cf8316b9. Alle eigenen Auswahl-/Wachhalteprozesse beendet. Veröffentlichung und Folgeauftrag ändern diese historischen Messergebnisse nicht.
