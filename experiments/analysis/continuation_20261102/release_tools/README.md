# Bedingte P-Abgabeprüfung: offline vorbereitet

Stand 02.11.2026. Die 9.000-Spiele-Bestätigung läuft noch. **Keine tatsächliche
Paketprüfung, technische Abnahme oder Installation durch diese Vorbereitung.**
V14 und die bestehende `Gruppe15.zip` bleiben unverändert.

## Geprüfter Umfang

`verify_P_package.py` prüft später das vollständige Laufzeitpaket, alle 36 Netze
und sämtliche Checkpointfelder. Der tatsächliche Aufruf ist bis zum vollständigen
Bestätigungsabschluss gesperrt, bevor Torch importiert wird. 16 synthetische
Tests bestanden bei Root (0,91 s); unabhängiger Review PASS nach engem
Kompatibilitätsfix. Der ursprüngliche Gegenbeleg und dessen erfolgreiche
Nachprüfung sind erhalten.

Im rohen V14-/P-Checkpoint fehlt der gespeicherte `frozen`-Schlüssel. Sein
effektiver Wert ist der quellengeprüfte Standard `False`. Das ZIP fügt ausdrücklich
`frozen=True` hinzu. Fehlend ist hier kein gespeichertes `False`; der Prüfer
unterscheidet beides. P verändert gegenüber V14 ansonsten ausschließlich die
beiden Planungsflags; das ZIP gegenüber P ausschließlich diesen Einfrierschalter.
Alle Tensorbytes, Datentypen, Formen, Reihenfolgen, Metadaten und anderen Felder
müssen exakt erhalten bleiben. Die Konfiguration enthält 74 gespeicherte Felder;
deren primitive Typen wurden zusätzlich anhand des tatsächlichen Manifests und
des Konfigurationsquelltexts geprüft, ohne Modelle zu öffnen.

`install_qualified_P.py` akzeptiert nur die strukturierten tatsächlichen
Auswahl-/Bestätigungs- und unabhängigen Auditbelege, unveränderte numerische
Gates sowie eine separate vollständige technische Abnahme. Kein künstliches
PASS-Log, keine Team-Ausnahme. Vor einer expliziten Installation: laufende Jobs
beenden, Originaldateien prüfen und dauerhaft sichern. Drei Dateien werden mit
Journal, exklusiver Veröffentlichung und geprüfter Rücknahme übertragen;
unerwartete fremde Dateien bleiben erhalten. Das ist keine simultane atomare
Umschaltung aller drei Dateien. 19 synthetische Tests bestanden bei Root (3,62 s),
zusätzlich sieben unabhängige Sicherheits-/Schematests; Review PASS.

Die Anleitung und das genehmigte Design beschreiben Datenvertrag, Sperren,
Installation und Rücknahme. Die Dateien sind bewusst auf diesen einen Kandidaten,
die alten V14-/ZIP-Hashes und die historische Studie beschränkt; kein allgemeines
Freigabewerkzeug. Codeabnahme ersetzt weder Leistungsmessung noch tatsächliche
Modell-, Kurs-, Python-3.10- und Replayprüfung. Eine bloß formal passende
Abnahme-JSON darf niemals als erfundener Prüfbeleg erzeugt werden.

## Separat vorbereitete Python-3.10-Umgebung

Nur außerhalb beider Repositories unter `/tmp/sherlock-continue-20261102/venv310/`:
Python 3.10.22, Torch 2.2.2, NumPy 1.26.4, LuxAI S3 0.2.1, JAX/JAXlib 0.4.35,
Gymnasium 1.4.0, macOS arm64. Das gemeinsame Python 3.13 und die eingefrorene
Auswertung wurden nicht verändert. Noch kein Agent darin ausgeführt.

Die Upstream-Engine verwendet fünf Matches; die Kursversion drei. Ausschließlich
die isolierte 3.10-`params.py` wurde bytegleich aus der bereits eingefrorenen
Kursversion übernommen; alle gebundenen Engine-Pythondateien stimmen überein.
Upstreamdatei und Installationslogs bleiben erhalten. Ein erster Versuch mit
ausschließlich Binärpaketen scheiterte an Gym; der zweite erlaubte dessen
Python-Paketbau und installierte die numerischen Pakete weiterhin als Binärpakete.
Die Interpreterinstallation meldete eine Dylib-Patch-Warnung für eventuelle
native Erweiterungsbauten; tatsächliche Importe und Ausführung müssen erst im
ruhigen Prüfzeitfenster bestätigt werden. Keine Windows-Laufzeitprüfung behauptet.
Verfahren: [offizielle uv-Dokumentation](https://docs.astral.sh/uv/guides/install-python/).

Alle Kopien sind durch `offline_provenance.json` bytegenau belegt. Historische
absolute `/tmp`-Pfade in den Receipts nicht nachträglich umschreiben. Erst nach
allen tatsächlichen Nachweisen darf Root einen neuen gebundenen Freigabebeleg
erzeugen. Bei gescheiterter Bestätigung bleiben diese Werkzeuge unbenutzt.
