# Laufzeitprüfung und fester 200-Karten-Zusatz

**Ergebnis:** Die ursprüngliche vollständige 300er-Bestätigung ist mit der gemessenen Geschwindigkeit bis 02.11., 05:30 Berlin **nicht belastbar planbar**. Der von Root vor Sichtung von Leistungsdaten fest entschiedene 200er-Zusatz ist methodisch vertretbar und zeitlich plausibel, sofern die späteren Jobs nicht deutlich langsamer werden. Keine Jobs gestartet/geändert, keine Quellen-/HEAD-/Gewichtsänderung, keine Gitmutation.

## Ausschließlich Zeit-/Fortschrittsbelege

Aus `selection_state.json` und gefilterten Ladezeilen: Baseline-Start 01.11., **21:11:11,840 UTC**, Child-Ende **21:36:44,023 UTC**, nächster Jobbeginn nach Journalprüfung **21:36:46,320 UTC**. Effektive volle Jobzeit rund **25 min 34 s** für 700 Spiele mit zwei Workern. Alle vier Self-Gegner erreichten je 100 Ladezeilen. Der V13-Abschnitt zeigte etwa 21–23 Spielstarts/min.

Nach Baselineabschluss wurden aus der CSV ausschließlich `opponent` und `secs` verarbeitet, **keine Sieg-, Punkte-, Resultat-, Delta- oder Konfidenzwerte**. Die 100 V13-Self-Spiele brauchten im Mittel 5,4963 s pro Spiel; mit zwei gleichmäßig beschäftigten Workern ideal 4,5803 min/100. Für Direktduelle gegen V14 wird vorsichtig **D ≈ 4,7 min/100 Spiele** angesetzt; V14 hat dieselben 36 Netze wie V13. Die gesamte Baseline hatte ideal aus Spielzeiten 25,1407 min, tatsächlich mit Laden/Anlauf/Balance rund 25,57 min. Direktduelle sind somit teurer je Spiel als der gemischte Paneldurchschnitt; bloß `9000/700 × Baselinezeit` unterschätzt sie etwas.

## Hochrechnung ohne Leistungsauswahl

Sei **T = 25,57 min** für 700 Panelspiele und **D = 4,7 min** für 100 Direktspiele. Alle drei Auswahlkandidaten vollständig, keine Streichung aufgrund von Zwischenständen:

| Bestandteil | Spiele | Rechnung | Geschätzte Zeit |
|---|---:|---:|---:|
| Gesamte Auswahl ab 21:11 UTC | 3.100 | 4T + 3D | 116,4 min |
| ursprüngliche Bestätigung, 300 Karten | 9.000 | 12T + 6D | 335,0 min |
| fester Zusatz, 200 Karten | 6.000 | 8T + 4D | 223,4 min |

Von Auswahlstart bis 05:30 Berlin stehen rund **438,8 min** bereit. Auswahl + ursprüngliche Bestätigung ergeben bereits **451,4 min**, nominell Ende **05:43 Berlin**, ohne technische Reserve. Für die 200er-Fassung sind es **339,7 min**, nominell Ende **03:51 Berlin**. Selbst mit vorsichtig pauschalen **20 % auf die gesamte Auswahl-/Bestätigungsrechnung** ergibt sich etwa **04:59 Berlin**, also ungefähr 31 Minuten Abstand zur 05:30-Grenze. Nur 20 % auf die noch folgende Bestätigung anzusetzen ließe mehr Luft.

Dies ist eine Laufzeitprognose, keine Erfolgsgarantie: 37 statt 36 Netze, Overlap-Mehrarbeit, andere Karten, Last/Temperatur und Job-/Validierungsaufwand können Zeiten verändern. Vor Bestätigungsbeginn nochmals aus tatsächlich abgeschlossenen Panel-/Direktjobs rechnen. Passt die **vollständige** neue Phase samt Reserve nicht mehr, auslassen; keine unvollständige Bestätigung verwerten. Höchstens zwei Worker bleiben verbindlich.

## Prüfung des 200er-Zusatzes

**Kein fachlicher Einwand unter den von Root genannten Bedingungen:** feste unabhängige Bestätigung auf **832000–832199**, getrennte Direktkarten **833000–833199**; dieselben sechs Gegner plus default und dieselben vollständigen gepaarten Spielschlüssel. Das sind 2×200×2×7 + 200×2 = **6.000 Spiele**. Die Entscheidung fällt vor erster Ergebnislektüre und vor dem ersten Bestätigungsspiel ausschließlich aus Laufzeitgründen.

- Unveränderte Stärkegates: Panel-Δ ≥ +1 pp und Untergrenze > 0; Solution-Δ ≥ 0 und Untergrenze ≥ −1 pp; default ≥ 99 % und Δ ≥ −1 pp; Direkt-Untergrenze > 50 %. Ganze Karten gepaart bootstrappen, 5.000 Ziehungen, Seed 0, gleiche Perzentile.
- **200 statt 300 Karten** heißt ein Drittel weniger Bestätigungsspiele und bei ähnlicher Varianz ungefähr **√(300/200) = 1,2247**, also **22,5 % breitere Intervalle**. Das ist keine halbierte Präzision. Power und Chance auf eine qualifizierte Verbesserung sinken; ein nicht bestandenes Ergebnis wird ehrlich beibehalten. Gegenüber dem historischen 800er-Battle bleibt dies ein eigenes kleineres Nachtprotokoll.
- Genau ein vollständig nominierter Kandidat, kein Nachrücken, kein Retry, keine Verlängerung nach Blick auf Konfidenzgrenzen. Niemals einen begonnenen 300er-Lauf rückwirkend bei 200 abschneiden oder je Gegner verschiedene Fallzahlen wählen.
- Neue Phase **`confirmation200`** mit vorab fixierten erwarteten Schlüsseln und n=200. Originalplan, laufender Auswahl-Freeze, HEAD und Spielquellen bleiben unverändert. Addendum und neuer Auswerter liegen **außerhalb sämtlicher vom Source-Freeze erfassten Pfade**, werden vorab gehasht und im Phasenmanifest eindeutig dem Originalplan zugeordnet. Ein neu angelegtes `.py` irgendwo im laufenden Repository würde bereits den globalen Source-Freeze verändern und ist daher ungeeignet.
- Auswerter muss die tatsächlichen Nachtgates umsetzen; ein unveränderter Aufruf der älteren historischen Gates wäre wegen anderer Solution-Grenzen kein Ersatz. Vor Bestätigung keine Outcome-basierte Nachjustierung des Zusatzes.

Dieser Bericht bestätigt die Bedingungen des beschriebenen Zusatzes, nicht die Existenz/Hashes noch zu erstellender Dateien oder eine bestandene Stärkenmessung. Beobachtung beendet; für spätere Remote-SHAs oder Abschlussaudits verfügbar.
