# Methodennotiz nach der Ausführung

Diese Notiz wurde nach den tatsächlichen Toolaufrufen erstellt. Sie ist kein damals gesicherter Producer und ergänzt keine fehlenden historischen Startnachweise.

Der Root-Launcher führte die vier in process.json gespeicherten Befehle aus, mit cwd=/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics und THREAD_ENV aus scripts.early_curriculum_study, unter dessen gemeinsamem resource_lock. Jede Stufe hatte ein neues Log und ein 600-Sekunden-Limit. Nach jeder Stufe wurden die geschützten Gewichts-/ZIP-Hashes erneut geprüft. process.json speicherte Exitcodes und Laufdauern, aber keine separaten cwd-/Startzeit-/Source-Snapshots. Dieser engere Umfang gilt weiterhin.

Der Payloadvergleich lief als inline Python im Root-Toolaufruf: ZIP88df und RawV14 98a073 wurden gehasht; 18 eindeutige ZIP-Einträge und CRC geprüft; die 14 Pythonmodule bytegleich mit git75af0c5 verglichen. Beide Checkpoints wurden mit Torch map_location=cpu/weights_only=True geladen. Die geprüften Funktionen config_schema, checkpoint_schema(...,frozen=False/True,defaults=defaults) und strict_equal aus verify_P_package.py verglichen Form/Dtype/UInt8-Tensorbytes/Metadaten und alle übrigen Felder. Erwarteter Paketinhalt war eine Kopie von RawV14 mit cfg.frozen=True. Kein P-Auditaufruf, keine Agentenkonstruktion oder Forward-Calls darin.

Ein erster inline Payloadaufruf hatte das inzwischen erforderliche defaults-Argument ausgelassen und war mit TypeError abgebrochen; er erzeugte keine Spiele und keinen erfolgreichen Prüfbeleg. Der korrigierte Aufruf bestand und erzeugte existing_zip_payload.json. Die separate Bibliotheksreparatur und der erste fehlgeschlagene Kursimport sind im Reparaturbericht erhalten.
