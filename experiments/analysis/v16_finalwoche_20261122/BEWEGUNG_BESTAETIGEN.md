# Wann ein Bewegungsversuch die Abgabe verbessern würde

Stand vor dem Abschluss der drei kleinen Spielvergleiche am 23. November. Jede Variante muss zunächst die Bedingungen ihres eigenen 40-Karten-Vergleichs erfüllen. Die Ergebnisse der Ausbildung, Replikation und Auswahl fließen mit null Stimmen in ihre unabhängige Bestätigung ein.

| Variante | Neue Karten ohne Auswahl nach Spielparametern | Hauptziel |
|---|---|---|
| Zwei Einheiten steuern dasselbe Punktefeld an | 160361000–160361119 | Mittlere Änderung der ganzen Spielsiege gegen Solution und Kaggle, beide Gegner gleich gewichtet |
| Gelernter Ertrag einer späten Bewegung | 160365000–160365119 | Dasselbe gleich gewichtete Siegmaß |
| Gelernter Sichtgewinn in der Eröffnung | 160370000–160370119 | Zusätzliche ganze Siege gegen Solution |

Je Variante spielen Kandidat und unveränderte V16 auf den beiden Startseiten aller 120 Karten gegen beide Gegner. Auf den ersten 40 dieser Karten kommen direkte Duelle von beiden Seiten hinzu. Das ergibt 1.040 vollständige Partien. Beim Sichtgewinn entscheidet weiterhin nur bei öffentlicher Sensorreichweite 1–2 der gelernte Berater. Alle anderen Karten verbleiben im Nenner.

Für jede Karte erst die gepaarten Differenzen ihrer Sitze mitteln. Bei der kombinierten Messgröße dann die beiden Gegner pro Karte mitteln. Für das zweiseitige 95-%-Intervall 20.000 Mal jeweils 120 vollständige Karten mit Zurücklegen ziehen (NumPy-Startwert 231150, lineare Perzentile). Die Untergrenze für das festgelegte Hauptziel muss **größer als null** sein. Gegen jeden externen Gegner mindestens ebenso viele ganze Siege wie V16 sowie wenigstens 40/80 direkte Siege. Ein Direktvorsprung wird nur mit einer unteren 95-%-Kartenintervallgrenze über 50 % als belegt bezeichnet. Bei mehreren qualifizierten Varianten werden sämtliche Ergebnisse einschließlich gescheiterter Vergleiche berichtet. Als weitere Absicherung bei mehreren gleichzeitigen Bestätigungen muss die Hauptgröße für eine Abgabeempfehlung auch ein Bonferroni-Intervall über die tatsächlich getesteten dieser drei Varianten bestehen.

Jedes Spiel hat genau drei Matches und 303 Umgebungsschritte, einen vollständigen Endstand und einen fehlerfreien Agenten auf beiden Sitzen. Bei externen Spielen ohne einen Eingriff müssen alle Endstände der entsprechenden V16-Partie entsprechen. Prüfstand, Gewichte, Kartenauswahl und Modellsignatur werden vor dem Start festgehalten. Ein unvollständiger Block bleibt offen. Ein positiver Vergleich führt zur getrennten Verpackung, Kursprüfung und Reproduktion, bevor das Team über die Abgabe entscheidet.
