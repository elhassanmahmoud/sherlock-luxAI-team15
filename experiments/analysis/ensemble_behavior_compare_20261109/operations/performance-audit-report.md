# Unabhängiger Endaudit: fester BEHAVIOR38-Vergleich

**Datenaudit PASS; kein Nominierter.** Der unveränderte vorbereitete externe Prüfer wurde genau einmal nach vollständigem Owner-/Workerende ausgeführt: Exit 0, stderr leer, **10.595 Checks, 554 Hashbindungen, 535 eindeutige gehashte Dateien**. Keine Modelle, Projektimporte, Netzaufrufe, Tests, Spiele oder Projektänderungen.

| Fester Job | W/D/L | Score und 95%-Ganzkartenintervall, soweit direkt |
|---|---:|---:|
| V14 gegen Solution | 39/0/1 | — |
| CONTROL38 gegen Solution | 40/0/0 | — |
| BEHAVIOR38 gegen Solution | 40/0/0 | — |
| BEHAVIOR38 direkt gegen V14 | 16/0/24 | 40 % [20; 60] |
| BEHAVIOR38 direkt gegen CONTROL38 | 12/0/28 | 30 % [10; 50] |

Die beiden Solution-Sieggates bestehen. Die beiden festen Direktgates **mindestens 24 echte Siege von 40** sind mit 16 beziehungsweise 12 verfehlt; `nominated=false`. Solution-Scorekontrast BEHAVIOR38 minus V14 **+2,5 pp [0; +7,5]**, gegenüber CONTROL38 **0 pp [0; 0]**, letzteres ausdrücklich degeneriert. Keine Bestätigung, Schwellenänderung, Ersatzspiele oder automatische Übernahme.

Alle **200 tatsächlichen CSV-Zeilen** unabhängig gelesen: fünfmal genau 40 eindeutige feste Gegner/Karte/Seite-Schlüssel, beide Seiten, 303 Schritte und Punktzählung v2. Vollständige Ergebnis-/Matchgewinn-/Punktarithmetik und endliche Metriken geprüft; keine Zeilen ausgeschlossen oder Schnittmengenlücken versteckt. Exakte Originalbefehle mit den unveränderten akzeptierten Modellpfaden, jeweils einem Worker und den drei festen 999er-Kohorten verifiziert.

Absolute W/D/L, vier Gates und sämtliche Solution-/Direktintervalle selbst mit NumPy nachgerechnet: je Statistik frischer PCG64/Seed0, 5000 Ziehungen ganzer Karten, beide Seiten zuerst je Karte gemeinsam gemittelt, feste 2,5-/97,5-Perzentile. Remis zählen im Score 0,5, in Sieggates nicht als Sieg. Alle nachgerechneten Summaryfelder einschließlich Degenerationsflags stimmen mit der Originalsummary überein; fester numerischer Vergleich 1e-12. Kein Aufruf der ursprünglichen Analyse.

Quelle **16fae8afd42dc6b9c721be4fe46a7595375e8628**, Admission, deklarierte Source-/Input-/Interpreter-/Schutzbindungen und aktuelle Modell-Bytehashes geprüft. Die akzeptierte tatsächliche Nullspiel-Montage samt unabhängigem Tensorbeleg und Rootannahme eng wiederverwendet; keine Archive erneut geladen. V14/ZIP unverändert. Seedannahme mit dokumentierten lokalen Grenzen gebunden, keine neue Kartensuche.

Vor Ausführung tatsächliches Ende von Owner **68921**, allen fünf Originalworkern **68934/68939/69254/69259/69659**, ihren Prozessgruppen und Wachhalter **69024** selbst geprüft. Owner complete/active leer, alle fünf Returncodes 0; dokumentierte 2/2/1-Wellen eingehalten. Originalgruppen nach Audit nochmals abwesend. Vollständige abgeschlossene Owner- und CSV-Dateien blieben während der Prüfung unverändert; Snapshots und Prästartbeleg extern gespeichert.

**Grenzen:** 40/40 auf diesem festen Block ist keine Garantie allgemeiner Solution-Überlegenheit; [0,0] erfasst unbekannte Kartenrisiken nicht. Deskriptive Intervalle, keine Korrektur für wiederholte Projektauswahl. Historische Kontrollen sind keine neu trainierten unabhängigen Replikate. Kein isolierter Kausalnachweis für Ensembleverhalten oder allgemeiner Unterlegenheitsbeweis aus den kleinen direkten Stichproben. Ohne Rohtraces keine erneute Engine-/Aktionsrekonstruktion; erfolgreiche unveränderte Originaljobs binden den Fehlerabbruch beider Spieler. Kein Weiterstart durch diesen Audit.

SHA256:

- Admission: `78a6e3d52c5722e13fe0cae55e8ff0bcf439ce05d74558338f652c0428a96b9b`
- Originalsummary: `1461df89c9f8b470739cb5a7f9849d758b6c8635237603027205a8e1f0fb3498`
- `results.json` und `run.log`: `86cb41759c61339fd97c3b0434524d17bb22bbf86e565c66a461c2321a41b867`
- `check.py`: `a30583fb079c779d5864d459b6bc71ee55cd6460154e8478ed44611db4332a52`
- `bindings.json`: `10f06b387d69dbdaa3c7d0c2391e2ab52b5956447d9234c90b4c09099c704cdc`
- `pre-execution.json`: `08be1f574dc6344ba943b099b2c6c64e3eafb813e10c68d0c0bd38037f9529ea`
