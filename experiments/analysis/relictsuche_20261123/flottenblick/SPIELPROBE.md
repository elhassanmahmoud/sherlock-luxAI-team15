# Tatsächliche zusätzliche Sicht im Kursverlauf

Auf **64 weiteren Karten mit beiden Startseiten** bekam ein zuvor wartendes, freies Schiff bei 98 von 128 Startplätzen eine geeignete Suchmöglichkeit. Zum Vergleich spielten das gelernte Modell, die im Training ausgewählte einfache Flottenprojektion und das ursprüngliche V16 insgesamt **384 Originalpräfixe**. Bei jeder Gelegenheit stimmten die öffentliche Vorgeschichte, die Ausgangsposition, die UID und die ursprünglichen Team- und Gegnerbefehle überein. Nach dem Start reagierten die übrigen eigenen Schiffe und der Gegner auf den jeweils wirklichen Spielzustand.

| Innerhalb der folgenden acht Züge | V16-Originalroute | Einfache Projektion | Gelernte Prognose |
|---|---:|---:|---:|
| Erstmals gesehene Spiegelpaare ausschließlich durch die gewählte UID, Summe | 148 | 1.409 | **1.465** |
| Je gepaartem Startplatz, einschließlich Plätze ohne Gelegenheit | 1,156 | 11,008 | **11,445** |
| Erstmals gesehene Spiegelpaare durch die ganze Flotte, Summe | 3.329 | 4.568 | **4.661** |
| Neuer direkter Reliktfund im kurzen Fenster | 14 | 13 | 13 |
| Erste eigene Gutschrift im kurzen Fenster | 14 | 17 | 17 |
| Geänderte Originalbefehle | 0 | 240 | 266 |

Zusätzlich zur einfachen Projektion erfasste das Netz **56 exklusive neue Spiegelpaare**. Im Mittel sind dies +0,438 je gepaartem Startplatz, mit einem gepaarten 95-%-Kartenintervall von −0,188 bis +1,219. Das Netz erfasste auf 14 Sitzen mehr, auf acht weniger und auf 106 genau gleich viele. Netz und einfache Projektion wählten auf 32 Sitzen unterschiedliche Wege. Die mittleren Punktsalden, die Zahl früher Reliktfunde und die Zahl erster Gutschriften innerhalb des kurzen Fensters stimmten bei diesen beiden Planern überein. Der große Abstand zur V16-Originalroute zeigt vor allem den Effekt, ein erneut wartendes Schiff überhaupt auf einen Suchweg zu schicken.

Die Vorbedingung für einen eigenen Ganzspielvergleich war ein positives Mittel beim tatsächlichen Zusatz gegenüber der einfachen Projektion zusammen mit der unabhängigen Verbesserung der Sichtvorhersage. Beide Voraussetzungen sind erfüllt. Das Intervall der tatsächlich zusätzlichen Spiegelpaare lässt auch einen kleinen Verlust zu. Über den Erfolg entscheiden die separat reservierten vollständigen Spiele gegen Solution und direkt gegen V16.

Über alle beobachteten achtzügigen Wirkfenster gab es keinen verschwundenen oder gesprungenen Scout-Slot. Bei normaler Sicht bestätigte eine Gegenprüfung auf zwei zuvor feststehenden kompletten Kursverläufen alle 9.696 ursprünglichen V16-Einheitenbefehle. Dabei wurde dieselbe Modellinstanz zwischen den beiden Seiten zurückgesetzt. Die Modellsignatur und die unabhängige Gegenrechnung sind archiviert.

[Ergebnisse und Intervalle](spielprobe.json) · [384 tatsächlich gespielte Verläufe und Befehlswechsel](spielzuege.jsonl.gz) · [Modellsignatur für die Spielprüfung](freigabe_spielpruefung.json) · [Normalsichtkontrolle](normalsicht.json) · [Gegenrechnung](nachrechnung.json) · [Eigenständiger Ganzspielplan](VERGLEICHSPLAN.md)
