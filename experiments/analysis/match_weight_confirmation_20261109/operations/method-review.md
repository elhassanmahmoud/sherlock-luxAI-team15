# Methodische Prüfung der einmaligen MATCH38-Bestätigung

Die vorgeschlagene begrenzte Bestätigung ist mit der präzisierten Aussage tragfähig: **Der Direktvergleich ist die primäre Bestätigungsfrage; das Viererpanel ist eine empirische Verschlechterungs- und Stabilitätswache.** Die bestehenden Gates können unverändert vorab festgeschrieben werden. Keine größere Ersatzstudie ist erforderlich. Die ursprünglich erwogene Bezeichnung des Panels als abgesicherter Populations-Nichtunterlegenheitsnachweis ist zu stark.

## Bedeutung der festen Gates

- **Direkt:** Mindestens 72 tatsächliche Siege in 120 Spielen und untere 95%-Ganzkarten-Scoregrenze strikt über 0,5. Ausgewertet werden 60 andere, frische Karten, jeweils mit beiden Seiten gemeinsam. Das bestätigt bei Bestehen einen Direkt-Scorevorteil nach dem vorab festgelegten Verfahren; Remis zählen 0,5. Es ist keine Garantie allgemeiner Überlegenheit und kein entsprechender Konfidenznachweis für die reine Gewinnwahrscheinlichkeit.
- **Panel:** Mittlerer gepaarter Scorekontrast mindestens 0 und untere Bootstrapgrenze mindestens −0,025; Solution und default jeweils mindestens so viele tatsächliche Siege wie V14; Square und rush jeweils höchstens zwei tatsächliche Siege weniger in 40 Spielen. Diese Bedingungen sind feste empirische Freigabekriterien. Sie beweisen weder allgemeine Nichtunterlegenheit innerhalb von 2,5 Prozentpunkten noch einzelne gegnerspezifische Nichtunterlegenheit. Gleichstand gegen Solution beweist keine Solution-Verbesserung.
- **Deckeneffekt:** Sind alle 20 Panelkartenkontraste null, ist auch jede Bootstrapstichprobe null und das Intervall degeneriert zu [0,0]. Das ist keine präzise Absicherung gegen ungesehene Kartenrisiken. Solche Intervalle ausdrücklich als degeneriert kennzeichnen; alle absoluten W/D/L und die Zahl unabhängiger Karten berichten. Auch sonst sind die Perzentilintervalle bei 20 Panelkarten approximativ.

## Unveränderter Rechenvertrag und materielle Schutzbedingungen

320 Panelspiele plus 120 Direktspiele ergeben genau 440 Spiele. Beide Modelle spielen dieselben 20 Panelkarten gegen alle vier Gegner auf beiden Seiten. Je Karte zuerst den gepaarten MATCH38-minus-V14-Scorekontrast über die acht Gegner/Seiten-Kombinationen mitteln; dann die **20 ganzen Karten gemeinsam über alle Gegner und Seiten** resampeln. Beim Direktvergleich die 60 ganzen Karten mit beiden Seiten resampeln. Je Statistik 5000 Ziehungen mit frisch gestarteter PCG64/default_rng(0)-Folge und festen 2,5-/97,5-Perzentilen. Keine Spielzeilen als unabhängige Stichproben behandeln.

Vor Datenaufnahme exakt binden: die frischen und disjunkten 20 plus 60 Karten, Ausschluss bekannter Trainings-, Screening- und Technikkarten, Modell-/Konfigurations-/Quellhashes sowie alle 440 festen Schlüssel. Grenzen des lokalen Kartenchecks bleiben offen. Alle Spiele müssen vollständig, korrekt gewertet, 303/v2 und ohne abgefangene Agentenfehler beider Spieler vorliegen. Keine Zeilen streichen oder ersetzen; Unterbrechungen bleiben unvollständig. Keine Zwischenstandsauswahl, Verlängerung oder Ersatzvariante bei Fehlschlag.

Alle Gates gelten gemeinsam. Inklusive und strikte Grenzen sowie eine feste Regel für reine Gleitkomma-Rundungsfehler vorab implementieren; keine nachträgliche Toleranzänderung. Keine Familienkorrektur oder simultanen gegnerspezifischen Konfidenzgarantien behaupten. Kein isolierter Kausalnachweis für w_match: Verglichen werden die vollständigen eingefrorenen Agenten MATCH38 und V14, nicht zusätzlich CONTROL38.

**Geeignete Formulierung bei vollständigem Bestehen:** „MATCH38 besteht die einmalige frische Direktbestätigung gegen V14 nach dem vorab festgelegten Karten-Bootstrap. Zugleich erfüllt es im definierten Viererpanel sämtliche empirischen Stabilitätsgrenzen. Das Panel belegt keine allgemeine Nichtunterlegenheit oder Solution-Überlegenheit; insbesondere degenerierte Intervalle bei Deckeneffekten begrenzen die Aussage.“

Reine methodische Prüfung vor neuen Daten. Keine Implementierung, Modelle, Spiele, Tests oder Freigabe ausgeführt.
