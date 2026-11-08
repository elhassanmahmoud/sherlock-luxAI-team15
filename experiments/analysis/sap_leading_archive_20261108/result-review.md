# Unabhängige Nachrechnung der gespeicherten SAP-Ereignistabelle

**PASS.** Tatsächlich ausgeführte, eigenständige Standardbibliothek-Nachrechnung: Exit0 in0,09s. Alle15 Zusammenfassungen stimmen exakt überein: insgesamt, beide Gruppen und jedes der zwölf Spiele. Keine erneute Ausführung des Diagnoseprogramms, keine Rohtrace-Vollzählung, Projektimporte, Modelle oder Spiele.

Input: `/tmp/sap-leading-archive-result-20261108.json`, SHA256 **`3f46764a597f13749a146977e5a7fee9611bed89bbb234ca9f93e6cad073016b`**, vor und nach der Nachrechnung bestätigt.

Eigenständiges ausgeführtes Prüfskript: [/tmp/sap-leading-result-check.py](/tmp/sap-leading-result-check.py), SHA256 `fd853f142c0c4d7e4e4448eda9cdbe7f50caeca46550a3c869b20ed305397780`. Aufruf: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sap-leading-result-check.py`.

## Bestätigte Nenner

| Zählebene | Finale SAPs | Geeignet | Folge beobachtet | Folge unbekannt |
|---|---:|---:|---:|---:|
| Alle Unit-Ereignisse |1343|426|370|56|
| Eindeutige Gegner/Frame-Fälle |—|286|248|38|
| Verlustgruppe, Unit-Ereignisse |762|183|163|20|
| Gewinnkontrollen, Unit-Ereignisse |581|243|207|36|
| Verlustgruppe, Gegner/Frame |—|120|109|11|
| Gewinnkontrollen, Gegner/Frame |—|166|139|27|

Der Unit-Funnel lautet1343→965→620→494→490→426→426. Alle Stufen, Ausschlussgründe und die getrennte Gegner/Frame-Deduplikation wurden aus den Ereignissen neu aggregiert. Keine doppelten Shooter/Frame-Schlüssel; wiederholte Schüsse auf denselben Gegner/Frame haben konsistente Folgelabel und Geometrie.

Von248 beobachteten eindeutigen Folgen: **118 weitergelaufen,81 andere kardinale Richtung einschließlich Umkehr,49 stehen geblieben,0 sonstige Bewegung**.38 unbekannte Fälle bleiben unbekannt; davon32 fehlende sichtbare UID und6 fehlender direkter Entscheidungsfolgeframe.

**Negative Folgeenergie bleibt beobachtet:**80 von370 Unit-Ereignissen beziehungsweise53 von248 eindeutigen Gegner/Frame-Fällen. Sie wurde weder entfernt noch in unbekannt umgedeutet. Ihre eindeutige Geometriedifferenz beträgt bei f=0,25 −8,25; zusammen mit +59,75 der195 nichtnegativen Fälle ergibt das unverändert +51,5.

## Neu berechnete Geometrie

Aus alten/neuen Zentren und gespeicherter Folgeposition erneut Chebyshev-Abstände und Gewichte gebildet; gespeicherte Distanz-/Bewegungslabels und jede einzelne Geometriezeile stimmen. Für die248 eindeutigen beobachteten Fälle:

| Fester Faktor f | Altes Zentrum, Summe | Vorhaltezentrum, Summe | Differenz |
|---|---:|---:|---:|
|0|49|118|+69|
|0,25|98,75|150,25|+51,5|
|0,5|148,5|182,5|+34|
|1|248|247|−1|

Mit Mehrfachschüssen als getrennten Unit-Ereignissen lauten die entsprechenden Differenzen +102/+76,25/+50,5/−1; sie dürfen nicht als zusätzliche unabhängige Bewegungsfälle gelten. Bei f=0,25 entfallen auf eindeutige Verlustgruppenfälle +13,5 und auf Gewinnkontrollen +38, bei f=0,5 +9 und +25. Die15 vollständigen Summary-Dictionaries einschließlich Energie-Untergruppen wurden auf exakte Gleichheit geprüft.

Kern des unabhängigen Standardbibliothek-Snippets (vollständige Nenner-/Gruppenprüfung im verlinkten Skript):

```python
from fractions import Fraction
FACTORS = {'0': Fraction(0), '0.25': Fraction(1, 4),
           '0.5': Fraction(1, 2), '1': Fraction(1)}

def geom(event):
    future = event['next_position']
    distances = [max(abs(a-b) for a, b in zip(center, future))
                 for center in (event['old_target'], event['predicted_target'])]
    result = {}
    for name, factor in FACTORS.items():
        old, new = [Fraction(1) if d == 0 else factor if d == 1 else Fraction(0)
                    for d in distances]
        result[name] = dict(old=float(old), new=float(new), delta=float(new-old))
    return result
```

## Interpretation und Grenze

Die selektierten alten Archivspiele enthalten geometrische Vorhaltegelegenheiten mit positivem Saldo für die drei vorab geprüften Faktoren0/0,25/0,5; bei f=1 entsteht kein positiver geometrischer Saldo. Faktoren sind feste Szenarien, keine geschätzten realen Streuwerte. Der positive Saldo ist kein Schadens-, Kausalitäts- oder Siegverbesserungsnachweis. Sichtbarkeits-/Überlebensselektion, nicht unabhängige wiederholte Situationen, mögliche UID-Wiederverwendung und andere Ziele/Reaktionen bleiben unaufgelöst. Die Fälle rechtfertigen allenfalls eine kleine, getrennt festgelegte Gegenfaktenprobe; keine automatische Modell-/Spiel- oder Regelübernahmefreigabe.

Diese Nachrechnung prüft die gespeicherte Ereignistabelle gegen ihre gespeicherten Zusammenfassungen sowie Koordinaten-/Labelarithmetik. Die öffentliche Auswahl aus ursprünglichen Frames, Rohtrace-Vollständigkeit und die tatsächliche Sichtbarkeit werden hier nicht nochmals rekonstruiert; dafür bleiben der vorangegangene Code-/Definitionsreview und die gebundenen historischen Tracebelege maßgeblich.
