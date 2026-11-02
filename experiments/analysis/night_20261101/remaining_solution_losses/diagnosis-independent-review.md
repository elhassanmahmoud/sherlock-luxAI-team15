# Unabhängiger Review der zwölf bekannten Diagnose-Nachspiele

**Vollständigkeit, Hashbindungen, vorhandene Reproduktionsbelege und die zentralen Prozentrechnungen stimmen. Keine konkrete Datenabweichung gefunden.** 524 kleine Prüfungen ausschließlich mit Standardbibliothek/CSV/JSON/SHA-256; keine Repo-/Torchimporte, Tests, Modelle, Spiele, Git-Aufrufe, Subagents oder Quell-/Gewichtsänderungen. Maschinenlesbarer Prüfbeleg: `diagnosis-independent-review.json` im selben Ordner.

## Umfang und Bindung

- Genau die sechs bereits bekannten Solution-Verlustschlüssel aus der ursprünglichen V14-Auswahl-CSV:831006/P1,831029/P0,831042/P0+P1,831043/P0+P1. Keine neuen Karten und keine zusätzlichen Gegenseiten.
- `matches.csv`: exakt36 eindeutige Schlüssel =6Spiele×3Matches×2Teams; korrekte Team-/Seitenbindung und Punktezählungv2. Die Summen der Matchpunkte und Matchsiege reproduzieren bei allen sechs Schlüsseln exakt die ursprünglichen Spielpunkte und1:2-Spielergebnisse.
- `mechanisms.json`: exakt dieselben sechs eindeutigen Spielschlüssel, je drei eindeutige Matchobjekte0/1/2, insgesamt18. Die ausgegebenen finalen Spiel-Matchsiege reproduzieren jeweils `[1,2]`.
- Beide Instrumentierungen spielen dieselben sechs Spiele nach: **12 Nachspiele,6 unterschiedliche Fälle**. Das ist keine Stichprobe aus12 unabhängigen Spielen.
- Alle Einträge in `outputs.sha256`, die Receipt-Ausgabehashes, die Eingabedateien einschließlich V14-SHA98a07350…d3d8 und ursprünglicher Auswahl-CSV sowie die gespeicherten Laufzeit-/Quellidentitätsdateien stimmen bei erneuter SHA-Lektüre. Preflight- und Execution-Identität stimmen überein. Beide im Receipt gebundenen Jobs haben Exit0 und den dokumentierten vollständigen Status.
- `lost_match_summary.csv` enthält exakt die12 tatsächlich laut CSV verlorenen Matches, keine zusätzliche oder fehlende Zeile. Die dort verwendeten Punkte, ersten Punktzeitpunkte, spätere Belegung und Wissenswerte stimmen mit den zugehörigen CSV-Zeilen überein; die Mechanismusanteile passen zu den verbundenen JSON-Objekten.

## Prozentwerte und ihre tatsächlichen Nenner

Alle folgenden Zahlen beziehen sich auf die **zwölf verlorenen Matches dieser sechs ausgewählten Niederlagen**. Sie sind Verhältnisse der aufsummierten Zähler/Nenner, kein ungewichteter Mittelwert von zwölf Matchprozenten.

| Kennzahl | Zähler/Nenner | Unabhängig berechnet | Textwert |
|---|---:|---:|---:|
| Unbekannte eigene Punktfeld-Schritte, im Umfeld eines bekannten Relics |2393/13666|17,5106%|17,5%|
| Unbekannte eigene Punktfeld-Schritte, ohne bekanntes Relic-Umfeld |516/13666|3,7758%|3,8%|
| Freie bekannte eigene Punktfeld-Schritte ohne Zielzuweisung |1681/4417|38,0575%|38,1%|
| Eigene Punktfeld-Einheitenschritte mit Energie unter Sapkosten |2837/6928|40,9498%|40,9%|
| Entsprechende gegnerische Punktfeld-Einheitenschritte |2043/7487|27,2873%|27,3%|
| Eigene Punktfeld-Einheitenschritte in Stacks |1241/6928|17,9128%|17,9%|
| Entsprechende gegnerische Punktfeld-Einheitenschritte |612/7487|8,1742%|8,2%|

Der Nenner13666 zählt wahre eigene Punktfelder über die erfassten Zustände, nicht verschiedene Felder, besetzte Felder oder ganze Spielschritte. Beide Informationsanteile verwenden denselben Nenner. Eigene Hälfte im Mechanismus umfasst die Diagonale (`x+y<=23`); die abweichende Hälfteinteilung des anderen Werkzeugs darf nicht stillschweigend gleichgesetzt werden. Die fehlende gegnerische Informationsklassifikation wird nicht als0 behandelt.

**Definitionspräzisierung für „frei“:** `free_pt_own` zählt im Agentenkontext bekannte eigene Punktfelder ohne eigene Unit und ohne sichtbaren Gegner. Unsichtbare Gegner können ein solches Feld tatsächlich besetzen. „38,1% nicht zugewiesen“ beweist deshalb weder tatsächliche Leere aller betroffenen Felder noch, dass Zuweisung allein deren Nutzung sicher ermöglicht hätte.

Die Energie-/Stacknenner zählen maskierte nichtnegative Einheiten auf wahren Punktfeldern nach rekonstruierter Bewegung. Niedrigenergie wird vor Sapbezahlung/-schaden beurteilt. Stacking zählt **alle Einheiten eines Stacks**, nicht nur die jeweils überzählige Einheit. Das sind die vorhandenen Messdefinitionen und keine nachträglichen kausalen Deutungen.

Zusätzlich unabhängig nachgezählt: In10/12 verlorenen Matches fällt der erste eigene Punkt laut CSV nicht später; die Belegung ab Schritt50 ist in12/12 niedriger. Haltertode151:141 und rekonstruierter ausgeteilter Sap-Schaden17567:12260 stimmen mit der Summe der zwölf verbundenen JSON-Matchobjekte überein.

## Bewusst erhaltene Ausgabegrenzen

- Kein Diagnosewerkzeug gibt einen tatsächlichen Gesamtstepzähler aus. Die303Steps/v2 sind eine Eigenschaft der ursprünglichen Benchmarkzeilen, kein jetzt aus diesen Diagnoseoutputs erneut bewiesener Stepgesamtwert.
- Das Mechanismus-JSON enthält weder Endpunkte noch Matchgewinner. Dort wurden ausschließlich ausgegebene finale Spiel-Matchsiege und Objekt-/Spielschlüssel reproduziert. Die Zuordnung „verlorenes Match“ stammt aus dem CSV und wird über identische Schlüssel verbunden; sie wurde nicht als eigener Mechanismus-Winnernachweis ausgegeben.
- Schäden, Energieflüsse und Todeszuordnungen sind rekonstruierte Begleitbilanzen. Punkt-/Siegreproduktion validiert sie nicht automatisch als vollständige oder kausale Ereigniszerlegung. Der erste Punkt im Mechanismus hat zudem eine andere Beobachtungszeitposition als `first_score_step` der CSV; der Text nutzt hierfür konsistent die CSV.
- Sechs gezielt ausgewählte bereits bekannte Niederlagen erklären mögliche Engpässe in diesen Fällen. Es werden weder Verlusthäufigkeit, neue Stärkeintervalle, garantierte Lösungsansätze noch eine Methodengeneralisierung abgeleitet.

Die abgeschlossene Bestätigungsentscheidung bleibt unverändert: Kandidat nicht qualifiziert, V14 bleibt. Dieser Diagnosebefund schafft keine neue Kandidatenzulassung, keine Gate-Ausnahme und keinen Auftrag zu weiteren Spielen oder Verhaltenseingriffen.
