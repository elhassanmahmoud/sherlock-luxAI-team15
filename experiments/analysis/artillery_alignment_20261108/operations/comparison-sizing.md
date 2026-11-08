# Empfehlung: 440 Auswahl + höchstens 600 Bestätigung

Für die neue Artilleriestudie empfehle ich **maximal 1040 Leistungsspiele**, vor Ergebnissen verbindlich festgelegt. Das spart gegenüber 440+1200 höchstens 600 Spiele beziehungsweise 36,6 %. Die frühere Fog-Studie und ihre Gates bleiben unverändert; ihre ungenutzte Bestätigung wird nicht nachgeholt. Ohne Nominierten endet auch diese neue Studie nach 440 Spielen.

**Auswahl, 440:** V14, CONTROL38 und ALIGNED38 gegen Solution92, sol92_sq und default auf denselben 20 frischen Karten, jeweils beide Seiten: 360 Spiele. Beide Kandidaten zusätzlich gegen V14 auf 20 separaten Karten, beide Seiten: 80. Beide festen 38er-Ensembles sind nominierbar; Mitglieder, Endcheckpoints und Gleichgewichtung bleiben fest.

Auswahlbedingungen wie im Fog-Protokoll: Zweierpanel Solution92/sol92_sq mindestens +2,5 Prozentpunkte gegenüber V14; Solution-Score und strikte Siege jeweils mindestens V14; default 40/40 strikte Siege; Direktspielscore mindestens 50 %. Genau einen Qualifizierten wählen: höchster Panelscore, dann meisten Solution-Siege, dann höchster Direktspielscore, vollständiger Gleichstand zugunsten CONTROL38. Ganzzahlige Halbsiegzähler verwenden. ALIGNED−CONTROL zusätzlich gepaart beschreiben; daraus mit zwei Trainingsstarts keinen isolierten Mechanismusnachweis ableiten.

**Bestätigung, genau 600:** Nur Nominierter und V14 gegen LOCAL_SIX plus default auf 20 neuen Karten, beide Seiten: 20×7×2×2=560. Nominierter direkt gegen V14 auf weiteren 20 neuen Karten, beide Seiten: 40. LOCAL_SIX ausdrücklich Solution92, sol92_sq, V3, V7, V10, V13; nicht das abweichende `BATTLE_SIX` aus der CLI verwenden.

Alle sieben bisherigen Bestätigungsgates erhalten:

1. Sechserpanel-Scoregewinn mindestens +1 pp.
2. Dessen untere 95%-Grenze strikt über null.
3. Solution-Scoreänderung mindestens −0,5 pp.
4. Deren untere Grenze strikt über −2,5 pp.
5. Defaultscore mindestens 99 %.
6. Defaultscoreänderung mindestens −1 pp.
7. Untere Direktspielscoregrenze strikt über 50 %.

Zusätzlich bleiben Solution-Score und strikte Siege mindestens V14 sowie default strikt mindestens 99 % erforderlich; hier bedeutet Letzteres **40/40 Siege**. Erfolg belegt unter diesem Prüfverfahren Panel-/Direktvorteil mit Solution-Schutz. Er beweist nicht automatisch einen separaten Solution-Zuwachs oder eine allgemeine 100%-Siegrate.

**Preis der Kürzung:** 20 statt 40 unabhängige Kartencluster; bei ähnlicher Kartenstreuung näherungsweise √2 größere Standardfehler. Kleine echte Gewinne werden häufiger unklar bleiben. Die 600er-Variante passt zum Wunsch nach weniger Spielen als feste Prüfung auf klare, konsistente Verbesserungen; eine quantitative Powergarantie lässt sich daraus nicht ableiten. Die 1200er-Alternative wäre empfindlicher, dürfte aber nur vor neuen Ergebnissen gewählt werden, niemals als Rettung nach 600.

Vier getrennte, vorab auditierte Kartenlisten; vollständige Schlüssel erzwingen. Ganze Karten samt beiden Seiten/Panelgegnern gepaart resampeln: 5000 Ziehungen, PCG64-Seed 0, 95%-Perzentile. Phasen nicht poolen. Kleine, diskrete Bootstrapintervalle garantieren keine simultane Deckung. FAIL/unklar: V14 behalten, keine Zusatzkarten, kein Nachrücker. Übernahme erst nach unabhängiger Datenabnahme, Sicherung und Kursreproduktion.

Grundlage: `docs/superpowers/specs/2026-11-08-fog-comparison.md`, `scripts/league_gates.py`, Auswahl-/Bestätigungsadapter `scripts/fog_reward_compare.py`. Rein lesender Methodenvergleich; keine Implementierung, Tests oder Modell-/Spielausführung.
