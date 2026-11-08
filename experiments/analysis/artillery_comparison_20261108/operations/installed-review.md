# Artillerievergleich: unabhängiger Installations-/Abnahmereview

**PASS, keine offenen Blocker im geprüften Umfang.** Vergleichsverfahren und bereits geprüfter STOP-Fix sind unverändert. Laufzeittests, tatsächlicher Kandidatenbau/-reload und späterer Leistungsvergleich sind nicht Gegenstand dieses Reviews und bleiben Root vorbehalten.

## Installation

Lesend gegen `/tmp/artillery-comparison-staging/` geprüft: `artillery_alignment_compare.py` unterscheidet sich ausschließlich durch die zwei nun echten SHA-256-Trustanchors. Evalskript, Testdatei, Spec und Plan sind bytegleich zur zuvor akzeptierten Stagingversion. Frühere Reviews `/tmp/artillery-comparison-review.md` und `...-fix1.md` gelesen. Kein neuer Gate-, Matrix-, Ranking-, STOP- oder Profilunterschied.

- Trainingsabnahme tatsächlich `34395fb96b8245a7cca7088cdb04acdd881dd1c037f9f7c0b688affb093f7712`.
- Frischeabnahme tatsächlich `9417e1526dfb29efa2e2ce8eca42486aa8a94c4f9118eab63712e22ab0676c21`.
- Installierter Comparecode `f9f2599deede9fa992cc08304f1cbbbd7758b42aba312aa30ea252b514e88056`.
- Evalcode `98a2adc7a19d8b2efaecaa242dd227702f9348ea40504480e950d727feced793`.
- Tests `fc9bd1716ec438e6420e7988ef4092fc5eb3c51ec3670fe8e3189ddc59d4fec1`.
- Spec `e3f0604189466b0fc41e738baea79fc295692ea15c3bb61c7fb51295b9905fdb`.
- Plan `38560693b04c238b7e1c8aa2bd256a75bc29060f27a814931616ac03a6dd397b`.

## Tatsächliche historische Trainingsabnahme

Die Abnahme enthält alle vier festen Arme, je Receipt plus neun Raw-/Modellartefakte, Startmanifeste/-gewichte, Supervisorstart/-ende, beide Paarbelege sowie unabhängige Daten-/Tensorberichte und Originalvalidatornachweis. Alle **58 Artefaktbindungen plus acht geschützte Bindungen** per SHA-256 gegen tatsächliche Dateien geprüft: **66 korrekt, null Fehler**.

Einzelbudgets 40 Vorlauf +400 Lernen +32 Diagnose =472 Ausführungen und60000 Updates; Gesamt1888/240000. Alle Berichte zeigen übereinstimmend Trainings-HEAD `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`, Manifesthash `b352abfa2b7f3f90eb66c0bae31bdd552ea190dc84045abd08d47afc98ab247e` und dieselben vier Receipt-Hashes. Datenstatus PASS_DATA_ONLY ohne Pending, Tensorstatus PASS_TENSORS_AND_REPLAY, Rootvalidator viermal PASS. Supervisor done, Queue/active leer, vier Exit0 und aufgezeichneter Wake-Abschluss. Abgabe-V14 und ZIP besitzen die unveränderten geschützten Hashes.

Dies ist die Bindungs-/Plausibilitätsprüfung der bereits separat ausgeführten Audits. Ihre Tensor-, Replay- oder Validatorberechnungen wurden hier nicht erneut ausgeführt.

## Frischebelege

Die akzeptierten vier exakten20er-Listen stimmen mit Spec/Adapter überein. Referenzkette Seedabnahme → Root-Auditannahme → komprimierter Rohscan plus Auditor/Markdown vollständig; sämtliche angegebenen Dateihashes stimmen. Gzipdekompression reproduziert exakt den dokumentierten unkomprimierten SHA-256 `f5320ed562080b87675b3523a4deb79f156d2932dc4e23a96be16f645f942a3f`.

Den vorhandenen Rohscan direkt gelesen: acht Worktrees, vor/nachher identische HEADs, null Verbrauchs-, Intervall-, Text-/JSON-Konflikte, null Scanfehler und null Mutationen. Bekannte seedlose/uneindeutige Daten und nicht erfasste externe Läufe bleiben explizit als Grenzen erhalten. Damit passt die begrenzte Aussage „keine beobachteten Konflikte“; keine unbelegte absolute Frischegarantie. Die vier gespeicherten Kartenlisten werden zusätzlich durch den vorgesehenen Builder/Plan-/Frischevalidator vor Start geprüft.

## Umfang

Nur Shell-/JSON-Lektüre, Dateivergleiche, SHA-256 und Gzip-Rückprüfung. Keine eigenen Python-/Modell-/Test-/Spielprozesse, keine Implementierungs- oder Repositoryänderung. Nur dieser Bericht unter `/tmp` wurde geschrieben. Keine Aussage über bestandene Root-Tests, Spielstärke oder Übernahme.
