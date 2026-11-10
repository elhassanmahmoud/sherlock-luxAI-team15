# Residualtraining abgeschlossen – noch keine Stärkeaussage

Zwei getrennte Starts61/62, je40 Vorlauf- und80 Lernspiele auf denselben60 Karten,
beide Spielerrollen. Pro fünf Karten drei gegen Solution_92 und zwei gegen
exakt den eingefrorenen36er-V14. Insgesamt240 Ausführungen,160 Lernspiele und
24.000 Updates. Zuvor acht technische Ausführungen. Quellenstand bd24e01.

Beide Vorläufe tatsächlich geprüft und vor dem ersten Update einzeln freigegeben:
140.532 bzw.141.702 Übergänge, identische Null-R-Initialisierung, leeres Adam.
Final je12.000 Updates, identischer letzter Online-/Targetstand nach Kopie,
endliche Tensoren und Verluste, je300.000 aktuelle Replayzeilen aus422.298 bzw.
424.175 gesamten Übergängen. Original36 unverändert, tatsächliches Wiederladen
beider Endmodelle und additive Inferenz geprüft. Sämtliche Ringbindungen,
Generationen und Vorlauf-Weltaktionslabels geprüft. Bestehende Rewards/Regeln
unverändert. [Tatsächliche Root-Abnahme](training/accepted.json).

Laufzeit beider paralleler Läufe rund9:45 Minuten einschließlich Vorlauf und
Prüfwartezeit; Lernabschnitt rund6:29 Minuten. Gemessene Prozessspitzen791/854MB.
Keine zusätzlichen Pilotspiele oder Zwischencheckpointwahl.

Auf je1.024 deterministisch gezogenen gespeicherten Situationen mittlere
absolute gemeinsame R-Verschiebung1,530/1,589 und aktionsabhängiger Anteil
0,171/0,179. Das ist eine Diagnose, kein Beweis besserer Aktionen. Mittlerer
Huberverlust der ersten/letzten100 Updates:0,765/0,769 und0,726/0,759; veränderte
Datenverteilung erlaubt daraus keine isolierte Lernfortschrittsaussage.
Rohvorschlags-/Regelzähler sind ausdrücklich nicht kausal interpretiert.

Endcheckpoint-SHA256:
- R61: `4302e796442caa88a5d4fc7a30b2cde603a070c830ad558f8edd3d0261febb16`
- R62: `5aef68e3179db607d539ca37b461c4f6cf0317ec72742b87fecee34bd58579cd`

End-/Vorlaufcheckpoints, Spielprotokolle, Verluste und Prüfbelege werden
versioniert. Die vier großen Replay-NPZs bleiben lokal in Studien- und Hauptkopie;
ihre Hashes stehen im Abschluss. Sie sind nicht als GitHub-Download verfügbar.
Keine Abgabegewichte ersetzt. Nächste Phase ausschließlich200 feste Auswahlspiele;
beide Starts müssen direkt mindestens24/40 gewinnen und gegen Solution
mindestens die neue gemeinsame V14-Baseline erreichen. Keine Verlängerung bei
Scheitern, keine automatische weitere Methode.
