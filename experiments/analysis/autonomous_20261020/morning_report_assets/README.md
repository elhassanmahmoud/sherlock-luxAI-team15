# Belege zur Ergebnisgrafik vom 21.10.2026

Die Grafik im [Morgenbericht](../../../../docs/MORGENBERICHT_20261021.md) vergleicht die drei festen Trainingsstarts und die unabhängige V4-Bestätigung. `figure_source.json` enthält die verwendeten Werte und Hashes der versionierten Quelldateien. Der unabhängige Review prüfte Daten, Budgetherkunft und Lesbarkeit; seine beiden sprachlichen Präzisierungen sind im Bericht berücksichtigt.

`render_figure.py.txt` ist der unveränderte historische Matplotlib-Renderer als Textsnapshot. Ausführung setzt das Repo als Arbeitsverzeichnis und Matplotlib/NumPy voraus; er schreibt die Grafik im Repo und eine Metadatendatei unter `/tmp`. Er ist keine Trainingsanleitung. Die im ersten Review vorgeschlagene Einordnung der früheren 18.000 Spiele als Teil der heutigen 66.000 war falsch: Die ursprünglichen `full`/`full_sym`-Läufe vom 10./11.10. sind andere Quellläufe als die heutigen `full_rules`-Läufe vom 19.10. Der Reviewer hat die Aussage im [dokumentübergreifenden Review](crossdoc_review.md) ausdrücklich zurückgenommen. Der Bericht trennt die drei Zahlen korrekt. Die dort gefundenen README- und Linkfehler wurden behoben.

Der [Review des nächsten Trainingsentwurfs](nextstep_review.md) trennt frische Einzelnetzpaare, Methodenbestätigung und spätere Ensembleübernahme. Diese Klarstellungen sind in der Übergabe ergänzt; es wurde keine neue Studie gestartet.

`documentation_audit.json` dokumentiert die vor Veröffentlichung geprüften Links, Quellen-/Gewichtsidentität und Archivdateien. `documentation_audit.py.txt` ist der damalige Prüfer als Textsnapshot mit lokalem Repo-Pfad; spätere reine Dokumentationscommits ändern den berichteten HEAD erwartungsgemäß. Der abschließende Prozess-/Automationsstand folgt im Arbeitsstand.
