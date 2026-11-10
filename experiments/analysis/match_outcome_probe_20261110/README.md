# Gepaarte Matchausgang-Probe

**Aktuell: Snapshotversuch technisch ungültig geschlossen.** 19 vollständige +1 teilweise Ausführung,10.203 Engine-Schritte. Baselineabweichung und unabhängig demonstrierte Set-Kopierreihenfolge; keine Lern-/Stärkenaussage aus alten Paaren. [Fehlerbericht](SNAPSHOT_FEHLER.md). Einmalige getrennte Präfixreparatur gemäß datiertem Zusatz in der Spec wird vorbereitet. Die folgenden Angaben dokumentieren die ursprüngliche Aufnahme, nicht einen weiterlaufenden Snapshotversuch.

Freigegebener Pilot aus docs/superpowers/specs/2026-11-10-match-outcome-selector-design.md.
Maximal32 Vollausführungen inkl4 technischer,48 Hauptpaare mit maximal5856 Fortsetzungsschritten und976 Wiederholungsschritten. Null Gradienten. Bekannte Entwicklungskarten, keine frische Leistungsbewertung.

- `technical/`: erste zwei Seed-/Seitenschlüssel, je Referenz/Sammler. Erst tatsächliche Root-Abnahme erlaubt `remaining/`.
- `remaining/`: weitere14 Schlüssel derselben eingefrorenen Quelle. Kein automatischer Übergang.
- Jede Manifestdatei bindet Quellen, Gewichtseingaben, Ausführungszähler und Rohdateien. Pro Paar negative/neutrale/positive tatsächliche Matchlabels; konkrete Auswahl einmal pro Match und Regeln unverändert.
- GateB: >=24 effektive Paare auf>=6Karten; GateC: >=3positive Matchflips auf3Karten. Machbarkeit, kein Stärkenachweis. Bei Verfehlung schließen, kein automatischer Nachschlag.

Stand vor Erststart:51 Tests und unabhängiger Kernreview abgeschlossen. Noch keine neuen Spiele oder Ergebnisse. V14/ZIP unverändert.
