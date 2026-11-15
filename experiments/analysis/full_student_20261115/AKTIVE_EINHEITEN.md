# Welche Lehrerbefehle können ausgeführt werden?

Die neuen Lehrerarchive enthalten auch Befehle für Einheiten, die Lux vor der nächsten Aktion entfernt. In den 24 Diagnosekarten sind mindestens **703 von 114.893 Zeilen** betroffen. Für den Vergleich der zwei trainierten Modelle ist der Effekt auf die **Differenz der Trefferzahlen exakt null**. Auf jeder möglicherweise betroffenen Zeile lässt die rekonstruierte Maske ausschließlich Stehenbleiben zu. Die absoluten Trefferquoten beziehen sich auf die archivierten Zeilen. Die spielbasierten Siege werden direkt aus dem Endstand ermittelt.

| Lehrerpartien | Zeilen | Energie als 0 gespeichert | Davon sicher echte 0 | Davon sicher negativ | Davon ungeklärt | Sicher negativ mit Lehreraktion STAY |
|---|---:|---:|---:|---:|---:|---:|
| Lernen, 216 Karten | 1.079.558 | 28.414 | 14.024 | 4.479 | 9.911 | 2.620 |
| Diagnose, 24 Karten | 114.893 | 3.234 | 1.552 | 703 | 979 | 300 |

## So lässt sich das aus den Originaldaten nachweisen

Lux speichert Energie als vorzeichenbehaftete ganze Zahl (int16). Positiv kann sie auf diesen Karten maximal 400 betragen. Eine Einheit mit Energie unter null erscheint noch in der letzten Beobachtung. Lux entfernt sie zu Beginn des nächsten Schritts vor dem Anwenden des Befehls. Eine Einheit mit exakt null Energie bleibt zu diesem Zeitpunkt aktiv. Beim ursprünglichen Lehrer-Sammler bestimmte allein die Sichtbarkeitsmaske, welche Einheitenzeilen ins Archiv gelangten. Die historischen V14- und Bewegungsschüler-Sammler prüften die tatsächliche Energie bereits vor der Aufnahme.

Merkmal 2 setzt jede negative Energie auf null. Der Audit prüft alle 401 Werte von 0 bis 400, für die sich die ursprüngliche nichtnegative ganze Zahl trotz Float16-Rundung rekonstruieren lässt. Eine archivierte Null braucht eine weitere Beobachtung. Dafür dient Merkmal 72 mit der Energiedifferenz zum nächsten sichtbaren Gegner. Die beiden Richtungsmerkmale liefern zusammen mit der eigenen Position dessen Feld. Zwei Einheiten können in demselben Schritt dasselbe gegnerische Feld als nächstes wählen. Auch bei gestapelten Gegnern nimmt das ursprüngliche Merkmal auf diesem Feld jeweils die erste gegnerische ID. Aus einer positiven eigenen Energie und der zugehörigen möglichen Differenz ergibt sich dann ein Intervall für die gegnerische Energie. Mit diesem Intervall und der Differenz einer nullkodierten Einheit lässt sich deren eigener Wert eingrenzen. Der Audit berücksichtigt die vollständigen ganzzahligen Differenzen zwischen −33.168 und +33.168 sowie die möglichen Float32- und Float64-Zwischenrundungen vor dem archivierten Float16. Nur eine strikt negative Obergrenze bestätigt eine ausgeschiedene Einheit. Eine Untergrenze von null bestätigt bei nullkodierter Energie eine lebende Einheit mit exakt null.

Beispiel aus Seed 7280000, Spieler 0, Archivframe 85. Für den nächsten Gegner von UID 13 ist die Energie genau 51, die gespeicherte Energiedifferenz erlaubt ausschließlich −92. Die Einheit hatte also −41 Energie. Ihr Lehrerlabel lautete STAY. Bei der Diagnose sind 300 der 703 sicher negativen Zeilen für jedes Netz ein garantierter Treffer. Die anderen 403 haben einen unzulässigen Lehrerzug und sind für beide ein garantierter Fehlwert. Die zwei Studienarme werden mit identischen 114.893 Zeilen bewertet. Die Differenz ihrer vollständigen Trefferzahlen gilt daher auch beim Ausschluss aller tatsächlich negativen Energien. Das Offline-Maß bewertet die maskierte Ausgabe des Netzes. Der Stillstandsabzug, das Entstapeln und die Einheitenwahl des Hybriden werden erst im Spiel angewandt.

Die ältere Trainingskontrolle, deren Checkpoint-Prüfsumme mit `fc5bb7f3` beginnt, trifft 35.886/51.048 volle Befehle in der V14-Diagnose, 108.438/156.243 auf Schülerstellungen und 81.091/114.893 auf Lehrerstellungen. Die legalen Schusszahlen im Checkpoint betragen 2.716, 6.313 und 3.895. Die Schussmaske sperrt SAP auf sämtlichen nullkodierten Zeilen. Alle 424 Lern- oder Diagnosekarten sind ihrer jeweiligen Partition eindeutig zugeordnet.

Beim Lernen werden unmögliche Lehreraktionen bereits entfernt. Ein zugelassener STAY-Befehl mit genau einer erlaubten Aktion hat Aktionsverlust null. Solche Lernzeilen können durch die Mittelung im Batch und die Schrittzahl das Training mittelbar beeinflussen. Eine Aussage über den Effekt eines erneuten Trainings folgt aus diesem Audit nicht.

## Weitere Datensammlungen

Der Sammler prüft jetzt vor dem Speichern `ctx["ally_ene"][uid] >= 0` anhand der ungerundeten Spielbeobachtung. Das gilt für neue gewöhnliche Lehrer- und DAgger-Sitzarchive. Das Metadatum `row_filter` kennzeichnet neu geschriebene Daten. Der historische Studienstand ist über die ursprünglichen Archivprüfsummen und die eingefrorene Sammlerversion weiterhin reproduzierbar.

Der Audit liest alle 705 Sitzarchive (368 historische und 337 neue), prüft ihre SHA-256-Werte und gibt die aufgeschlüsselten Zähler sowie einzelne überprüfbare Beispiele als JSON aus. Vom Repository-Stamm mit der Projekt-Python-Umgebung ausführen. Falls die Archive in einer anderen Arbeitskopie liegen, den letzten Pfad entsprechend setzen.

```bash
python experiments/analysis/full_student_20261115/pruefe_aktive_einheiten.py experiments/imitation
```

[Archivbefund mit allen Kohorten](aktive_einheiten.json) · [Ergebnisprüfung](../../../scripts/full_student_gate.py) · [Merkmale](../../../agents/sherlock/features.py) · [Sammler](../../../scripts/imitate.py)
