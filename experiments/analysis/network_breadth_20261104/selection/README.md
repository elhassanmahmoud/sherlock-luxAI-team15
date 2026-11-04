# Einzelnetz und 42 Netze: Auswahl abgeschlossen

Die vollständige Auswahl lief am 04.11.2026 von 08:22:38 bis 08:54:56 Uhr (Berlin) am eingefrorenen Quellstand `bed06df3335caa4d7a79c928132143a9c7e0a8fc`. Alle 920 Spiele endeten fehlerfrei. Sie verwenden 20 zuvor lokal unbenutzte Karten (861000–861019), jeweils beide Seiten, Kursmodus mit 303 Schritten und Punktezählung v2. Es sind 20 unabhängige Karten, nicht 920 unabhängige Karten.

| Variante | Sechserpanel | Solution | default | Direkt gegen V14 | Auswahl |
|---|---:|---:|---:|---:|---|
| V14 (36 Netze) | 190/240 = 79,17 % | 35/40 = 87,5 % | 40/40 | – | Referenz |
| SOLO28 (1 Netz) | 137/240 = 57,08 % | 31/40 = 77,5 % | 40/40 | 16/40 = 40 % | verworfen |
| FO42 (42 Netze) | 193/240 = 80,42 % | 39/40 = 97,5 % | 40/40 | 20/40 = 50 % | einziger Nominierter |

FO42 erfüllt alle vier vorab festgelegten Auswahlbedingungen. Die Paneldifferenz beträgt +1,25 Prozentpunkte, das gepaarte 95-%-Bootstrapintervall [−5,42; +7,51]. Gegen Solution beträgt die Differenz +10 Punkte [0; +22,5], das Direktduell-Intervall liegt bei [30; 70] %. Diese kleine Auswahl ist **kein bestätigter Stärkegewinn**, keine Freigabe und kein 100-%-Beleg. Die absolute V14-Quote auf diesen 20 Karten ist nicht direkt mit früheren Tests über 800 Spiele vergleichbar.

Das getestete einzelne Netz schneidet deutlich schlechter ab; daraus folgt keine allgemeine Aussage über alle Einzelnetze. FO42 ergänzt sechs anders trainierte FO-Netze. Der Test trennt deren Zusammensetzung und Anzahl nicht voneinander. Alle drei Varianten verwenden dieselbe V14-Spielkonfiguration. In dieser Studie wurde kein neues Netz trainiert.

Die [unabhängige Daten- und Statistikprüfung](../selection_review/selection_independent_review.json) stimmt mit der offiziellen Auswertung überein. Die ursprünglichen Pins und Startreviews liegen daneben. Ganze Karten mit beiden Seiten und allen Panelgegnern werden gemeinsam resampelt: 5.000 Ziehungen, PCG64 mit Seed 0. Vor der Bestätigung wurde der lokale Datenbestand erneut geprüft: keinerlei beobachteter Verbrauch der zurückgehaltenen Bereiche 862000–862399 und 863000–863159. Seedlose oder undokumentierte externe Versuche bleiben unbekannt.

Die **einzige Bestätigung mit FO42** lief am 04.11. von 09:00:13 bis 11:13:00 Uhr (Berlin): 3.840 Spiele, 80 Panel/default-Karten, 400 Solution-Karten und 160 separate Direktkarten, mit denselben eingefrorenen Quellen und Gewichten. FO42 verfehlte drei von sieben Übernahmebedingungen; V14 und die bestehende ZIP bleiben unverändert. [Abschließendes Ergebnis](../confirmation/README.md). SOLO28 wird nicht nachnominiert.

Diese Kopie archiviert abgeschlossene Daten. Absolute Pfadfelder geben deren tatsächlichen ursprünglichen Entstehungsort an. Die abgeschlossene Bestätigung nicht aus dieser Archivkopie neu starten. Das Manifest im Nachweisordner prüft die Originalbytes, inklusive unverändertem CSV-CRLF und bytegenauem Gzip-Inhalt.
