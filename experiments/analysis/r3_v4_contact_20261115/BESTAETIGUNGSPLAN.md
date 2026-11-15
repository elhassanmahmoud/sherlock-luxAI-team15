# Unabhängige Bestätigung des öffentlichen Kontaktwechsels

**Freischaltung.** Voraussetzung ist das vollständig bestandene 352-Spiele-Screening aus PLAN.md. Dafür zählen die tatsächlichen ursprünglichen Spiel-, Sitz-, Gegner- und Modellbindungen. Diagnose und Auswahl fließen nicht in die Bestätigungsquote ein. Die beiden unabhängigen Blöcke liegen im freigegebenen Nachtbereich und überschneiden sich weder mit der Auswahl noch miteinander. Bei der Festlegung fanden sich dort keine älteren Referenzspiele.

**Primäre Prüfung gegen die offizielle V14.** 60 Karten 7170500–7170559 mit beiden Sitzen. V14 und Kontakt spielen je 120-mal gegen Solution und 120-mal gegen den nativen Kaggle-Agenten. Weitere 60 Karten 7170600–7170659 mit beiden Sitzen ergeben 120 Direktspiele Kontakt gegen V14. Genau 600 Partien. Es gelten die etablierten drei Kriterien:

- Die untere 95-%-Grenze der externen Siegquotendifferenz Kontakt minus V14 liegt über null. Pro Karte bleiben die beiden Gegner und beide Sitze beim Ziehen zusammen.
- Die untere 95-%-Grenze der direkten Siegquote liegt über 50 %. Pro Karte bleiben beide Sitze zusammen.
- Der Kontaktagent gewinnt mindestens so viele Solution-Partien wie V14.

95-%-Perzentilintervalle, 10.000 Kartenstichproben, PCG64 mit Startwert 2711. Wir berichten separat, ob alle 120 Solution-Spiele gewonnen wurden und auf wie vielen der 60 Karten beide Sitze gewonnen haben. Ein perfekter Testblock beschreibt die beobachteten Partien. Er beweist keine allgemeine Siegquote von 100 %. Bei Scheitern der primären V14-Prüfung endet die Studie nach diesen 600 Spielen.

**Zusatzvergleich mit den Eltern.** Erst wenn die primäre V14-Prüfung positiv ist. R3 und v4 mixed spielen auf denselben 60 externen Karten und beiden Sitzen gegen dieselben zwei Gegner (je 240 Partien). Die Kontaktpartien der primären Prüfung werden direkt wiederverwendet. Externe Differenzen werden für jeden Elternvergleich wie bei V14 gepaart ausgewertet; hinzu kommen Solution-/Kaggle-Zähler, Verbesserungen und Verschlechterungen je Sitz sowie Matchsummen. Eine untere externe Grenze über null und wenigstens gleich viele Solution-Siege rechtfertigen die entsprechende Aussage zum jeweiligen Elternteil. Der Vorteil gegenüber V14 wird getrennt berichtet und beurteilt. Eine im Elternvergleich unsichere Differenz ändert dessen primäres Urteil nicht. Maximal 480 zusätzliche Partien; keine direkten Elternwiederholungen.

**Ausführung.** Unveränderte Spielquellen und Elterngewichte aus der Reproduktion der Vorauswahl verwenden. Zwei feste Spuren nach Kartenoffset modulo zwei sind für seriellen oder parallelen Start vorbereitet: genau ein Spielprozess je Spur, kein Unterprozess-Pool. Jede abgeschlossene Spur bindet sämtliche Ergebnisdateien einzeln per SHA-256. Innerhalb angefangener Spuren werden geprüfte vorhandene Zeilen wiederverwendet. Die zweite Stufe verlangt ein vollständig nachvollzogenes und gesichertes positives V14-Ergebnis. Jede etwaige Übernahme wird zusätzlich mit dem dann tatsächlich gemeldeten Kursagenten und seiner Kursprüfung abgeglichen.

Nach positivem Screen im Bestätigungs-Snapshot beide V14-Spuren getrennt starten; `STUDIE` enthält die ursprünglichen Verzeichnisse `sentinel`, `diagnosis` und `screen`. `BEST` ist ein separates Ergebnisverzeichnis.

```sh
"$PY" -B -u -m scripts.r3_v4_contact_confirm v14 --lane 0 --repo "$REPO" --selection "$STUDIE" --out "$BEST"
"$PY" -B -u -m scripts.r3_v4_contact_confirm v14 --lane 1 --repo "$REPO" --selection "$STUDIE" --out "$BEST"
"$PY" -B -m scripts.r3_v4_contact_confirm_assess v14 --repo "$REPO" --selection "$STUDIE" --out "$BEST"
```

Die Kommandos für die zusätzliche Elternstufe verwenden `parents` an Stelle von `v14`. Der protokollierte positive Primärbericht und alle Primär-Rohdaten werden vorher erneut validiert. Die Auswertung legt den separaten Ergebnisbericht im Verzeichnis `BEST` ab.
