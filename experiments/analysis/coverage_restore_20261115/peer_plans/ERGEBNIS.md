# Was die geplanten Züge der Mitspieler über den Lehrerzug verraten

Auf den 32 zurückgehaltenen Karten gab es 74.832 Einheitsentscheidungen, bei denen V14 und Lehrer unterschiedlicher Meinung waren und der Lehrer in eine der vier Richtungen ziehen wollte. Mit den zusätzlich geplanten Mitspielerpositionen traf der Häufigkeitsschätzer in 5.667 Fällen die Lehrerrichtung, die kontrollierte Vergleichstabelle in 5.315. Das sind 352 netto verbesserte Richtungen, von 7,10 auf 7,57 Prozent. Das gepaarte 95-%-Kartenintervall für die Differenz liegt bei **+0,34 bis +0,59 Prozentpunkten**. 29 Karten verbesserten sich, 2 verschlechterten sich, 1 war unverändert. 468 frühere Richtungsfehler wurden korrigiert, 116 frühere Treffer gingen verloren.

| Diagnosegruppe | Karten | Richtungszeilen | Zusatzeffekt bei widersprechender Lehrerrichtung, pp | Genauigkeit aller Klassen, pp | Logverlustdifferenz, nats |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alle | 32 | 74.832 | +0,470 | +0,021 | −0,00133 |
| Ursprüngliche V14-Stellungen | 8 | 17.487 | +0,526 | +0,182 | −0,00210 |
| R1/DAgger-Stellungen | 24 | 57.345 | +0,453 | −0,032 | −0,00109 |
| Gegen Solution | 10 | 25.654 | +0,487 | +0,057 | −0,00353 |
| Gegen Kaggle3 | 11 | 22.156 | +0,659 | −0,007 | +0,00266 |
| Gegen V14 | 11 | 27.022 | +0,300 | +0,008 | −0,00233 |

Die Vorhersage nahm das Maximum über alle sechs Aktionen, auch auf den Richtungszeilen. Die Kennzeichnung eines Lehrerwiderspruchs diente erst der nachträglichen Auswertung. Die geplante Belegung unterschied sich auf 29.514 von 207.291 Diagnosezeilen in mindestens einer der beiden groben Zählklassen von der physischen. Alle tatsächlich aufgezeichneten V14-Schritte waren nach Energie, bekannter Geländekarte und Grenzen legal. Es wurden nur andere eigene, aktuell handlungsfähige Schiffe gezählt. Auf 253 Diagnosezeilen standen laut öffentlicher Karte zusätzlich sterbende eigene Einheiten am Ursprung; für solche Schiffe speichert der Sammler keinen Plan.

Über alle 207.291 Zeilen kamen 43 korrekte Klassen hinzu (1.018 Korrekturen, 975 neue Fehler). Das gepaarte Kartenintervall −0,071 bis +0,106 pp ist mit einem allgemeinen Gleichstand vereinbar. Beim durchschnittlichen Logverlust 1,21772 → 1,21639 umfasst das Intervall −0,0050 bis +0,0028 ebenfalls null. Auf R1-Stellungen gingen netto 50 Gesamttreffer verloren. Die vorab festgelegte Signalbedingung für Richtungswidersprüche ist erfüllt. Die Bedingung gruppiert anhand der nur nachträglich bekannten Lehrerentscheidung; sie dient nicht als Auslöser im Spiel. Der Befund erlaubt, beide groben Zählwerte später als optionale Eingabe gegen denselben Schüler ohne Zusatz zu prüfen, und rechtfertigt keine ungeprüfte Bewegungsregel.

## Reproduktion

Alle 368 historischen Sitzarchive wurden anhand der veröffentlichten Einzelprüfsummen geprüft. Ein Prozess, ausschließlich NumPy, weder trainiertes Modell noch Kursengine geladen. Die Ausgabedatei enthält sämtliche 64 Diagnosesitze, Aufschlüsselung pro Gegner und Herkunft, Rohzähler und Kartenintervalle. Die synthetische Kontrolle im Skript prüft Selbstabzug, doppelte Belegung, Schuss, Rand, Asteroid und Energiemangel.

```bash
PY=/pfad/zum/hauptcheckout/.venv/bin/python
R=/pfad/zum/studiencheckout
D=/pfad/zum/hauptcheckout/experiments/imitation
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  "$PY" coordination.py "$R" "$D" neue_nachrechnung.json
```

Skript-SHA-256 `dfb3fc5cf563ee380f6e95b3fe0effb6ce59bf57fd5eb866b6fa0507f896c328`, Ergebnishash `83221b2d538650f7c5957b03eda98bd366291b1dc15d3c2df9dc561ba111c4b8`. Der ursprüngliche Plan und die vor dem Fit geklärte Eigenheit der öffentlichen Belegung sind in `PLAN.md` und `FORMAT.md` festgehalten.
