# Abgeschlossene erste Teilwelle

Diese Dateien sind Forschungsergebnisse, keine Abgabe und kein zugelassener PT-Kandidat.
Zwei vollständige Arme aus V14-Komponente 18 enthalten jeweils 120 Vorlaufspiele,
600 Lernspiele und 96 bekannte Validierungsspiele. Die unabhängige Abnahme steht
unter `../../performance/review/first_wave_independent_audit.md`.
Ohne das vollständige zweite Paar für Komponente 19 bleibt PT unzulässig.
Es werden ausschließlich Endstände aufbewahrt; aus `weights_best` wurde nichts gewählt.

Die Rohdaten im JSONL-Format sind verlustfrei mit gzip gepackt. `provenance.json`
bindet Original- und Archivhashes. `end.pth` enthält den exakt gespeicherten
Endzustand einschließlich Adam-Optimierer. Die Replay Buffer mit jeweils 187 MB
und ungenutzte Zwischenstände bleiben lokal.

Insgesamt 1.632 tatsächlich ausgeführte Spiele, davon 1.200 Lernspiele,
240 Vorlaufspiele und 192 bekannte Validierungen. Hier sind keine frischen
Leistungsspiele auf Karten ab 841000 enthalten.
