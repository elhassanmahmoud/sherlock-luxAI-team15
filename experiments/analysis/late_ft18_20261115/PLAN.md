# Bewegungswahl nach dem ersten Match

## Warum genau diese 18 Netze?

Die frühere unabhängige Bestätigung von FT18 liefert einen seltenen belastbaren Direktbefund: Die zuletzt trainierten 18 V14-Mitglieder gewannen 453 von 800 Duellen direkt gegen die vollständigen 36. Gegen Solution gewannen sie nur 755/800, V14 gewann 761/800. Trotzdem gewannen die 18 Netze 22 Sitzpartien, die V14 verlor, und verloren im Gegenzug 28 frühere V14-Siege. Diese alten Endergebnisse lassen offen, ob bereits die Erkundung im ersten Match oder Entscheidungen später im Spiel dafür verantwortlich waren. [Ursprüngliche Bestätigung](../final_battle_20261103/performance_confirmation/README.md)

## Eingriff im Agenten

Match 1 wird durchgehend mit dem normalen V14 gespielt. Ab Match 2 werden aus den bereits ausgewerteten 36 Netzen zwei Mittelwerte gebildet: wie bisher alle 36 sowie zusätzlich die Mitglieder mit den nullbasierten Indizes 18–35, genau wie beim historischen FT18. Erst die übliche Legalitätsmaske anwenden. Nur wenn beide Netzauswahlen eine Bewegung oder Stehenbleiben vorschlagen, wird der Vorschlag der 18 Mitglieder übernommen. Danach folgen unverändert die normalen Regelschritte. Ein späterer Regelschritt kann die geänderte Präferenz überstimmen. Die Variante braucht keine zusätzliche Netzdatei und erfährt nicht, wer ihr Gegner ist.

## Gezielte Entwicklungsprobe gegen Solution

Vierzehn historische Dev-A-Karten, je beide Seiten: alle zehn Karten mit mindestens einer V14-Niederlage sowie die vier nach Seed ersten anderen Karten mit zwei Siegen. Das sind zwölf bekannte Niederlagen und 16 Siege. In genau 28 Referenz- und 28 Variantenspielen werden alle Befehle beider Spieler im gemeinsamen ersten Match gehasht und der Matchstand kontrolliert. Die Kontrollergebnisse müssen die historischen Siege und Punkte reproduzieren. Technische Abweichungen vor einer Interpretation aufklären. Die Auswahl ist bewusst mit schwierigen Partien angereichert. Eine beobachtete Prozentzahl ist daher keine allgemeine Siegquote.

Eine frische Prüfung folgt nur bei mindestens drei geretteten ganzen Spielen auf mindestens zwei Karten, höchstens einem zuvor gewonnenen Spiel, das verloren geht, und mindestens gleicher Matchsiegsumme. Andernfalls wird diese Variante abgeschlossen. Die Entscheidung verwendet ganze Partien, nicht die Zahl veränderter Empfehlungen.

Bei Bestehen: 16 frische Karten 7274000–7274015, beide Seiten gegen Solution, Kaggle3 und direkt gegen V14; dieselbe V14-Referenz gegen beide externe Gegner. Mindestens zwei zusätzliche externe Siege, mindestens ein zusätzlicher Solution-Sieg, höchstens ein Kaggle-Sieg weniger und mehr als 16/32 direkte Siege sind für eine unabhängige Bestätigung erforderlich. Dort werden 60 neue Karten 7274100–7274159 extern und 7274200–7274259 direkt gespielt. Gegen Solution muss die untere gepaarte 95-%-Grenze für den Vorteil über null liegen, über beide externen Gegner zusammen ebenfalls; direkt muss die untere Grenze der Siegquote über 50 % liegen. Die 10.000 Bootstrap-Stichproben (Seed 2711) ziehen immer ganze Karten. Anschließend würden die üblichen Default- und Paketprüfungen folgen.
