# Curriculum: abgeschlossenes Paar s47

Erstes von drei vorab festgelegten Trainingspaaren, eingefrorener Quellenstand `a5d2e61b0e8654bad64e31c29447ada1e439174d`. Alle anderen Studienphasen laufen weiter; dieser Zwischenbericht ist keine abschließende Methodenentscheidung.

Je Arm3.000 Trainings-,160 Zwischenvalidierungs- und240 finale Auswertungsspiele auf60 bekannten Karten500720–500779, beide Seiten/default/Solution_92. Gegen Solution_92 frühe Variante62/120, Kontrolle86/120, Differenz−20pp, gepaartes95%-Kartenintervall[−32,5;−7,5]. Default119/120 gegen120/120. Einzelnetze, kein Vergleich mit der aktuellen18-Netz-Abgabe.

[Unabhängige Prüfung](independent_audit.md), [maschinenlesbare Befunde](independent_audit.json), [separate Root-Nachrechnung](root_counts.json). Initialidentität,32Startvalidierungen und erste100Trainingsspiele stimmen exakt in Nichtzeitfeldern überein. Geplanter Gegnerlabeltausch und gleiche Gesamtgegnerzahlen verifiziert. Keine Modelle für den unabhängigen Datencheck geladen.

[Abgeschlossene Phasen](completed_phases.json) enthalten die ursprüngliche Laufumgebung und Hashbindungen. [Kopiermanifest](archive_manifest.json) bindet die unveränderten Ursprungsdateien an Archivpfade. Ursprüngliche absolute Pfade in Metadaten bleiben absichtlich erhalten. Roh-Trainingsdateien liegen unter `experiments/runs/20261021_early_contact_v1_early_curriculum_s47_{control,early}`. Nach bestehender Git-Regel bleiben rohe `.pth`-Checkpoints lokal; Kopien sind in der Hauptarbeitskopie vorhanden, Replaybuffer nur in der eingefrorenen Arbeitskopie. Kein Abgabeersatz.

Die archivierte Prüfquelle `independent_audit.py.txt` ist der unveränderte damalige Datencheck mit lokalen Pfaden; vor einer Ausführung auf einem anderen Rechner in eine eigene Datei kopieren und Pfade bewusst anpassen. Die jetzige Studie weiterhin ausschließlich in ihrer eingefrorenen Arbeitskopie prüfen.
