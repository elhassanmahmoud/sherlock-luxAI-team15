# Begrenzter Artillerie-Leistungsvergleich

## Verbindlicher Umfang

Diese Ausführung konkretisiert die vor Ergebnissen festgelegte [Artillerie-Studie](2026-11-08-artillery-alignment.md) und den [Größenvermerk](../../../experiments/analysis/artillery_alignment_20261108/operations/comparison-sizing.md). Genau 440 Auswahlspiele; nur bei Nominierung höchstens eine frische Bestätigung mit genau 600 Spielen. Insgesamt höchstens 1040 Leistungsspiele. Frühere Studien bleiben geschlossen. Weder schlechte Ergebnisse noch breite Intervalle erlauben zusätzliche Karten, Nachrücker, Umgewichtung oder eine zweite Bestätigung. V14 und ZIP bleiben bis zu belegtem Vorteil und vollständiger Übernahmeprüfung geschützt.

## Trainingsabnahme und feste Kandidaten

Vier vollständige Arme control43/aligned43/control44/aligned44 müssen unter ihrer ursprünglichen Quelle `02ce1b2ce9a5b0780da1ee6462a2368b2226d495` technisch akzeptiert sein. Pro Arm 40 Vorlauf-, 400 Lern- und 32 Diagnoseausführungen, 60000 Updates und env_steps193320; insgesamt 1888 Ausführungen und 240000 Updates. Beide Vorlaufpaare müssen vor Gradienten anhand der Rohdaten angenommen worden sein. Unterschiedliche spätere Trajektorien sind erlaubt und erwartet.

Der ursprüngliche `artillery_alignment_study.validate_final_receipt` bleibt unverändert. Root führt ihn nach Ende aller vier Arbeiter noch unter der Trainingsquelle aus; sein Beleg bindet jeden Receipt-Hash und die Zähler. Ein unabhängiger Datenbericht mit `PASS_DATA_ONLY` bestätigt Rohdaten und Herkunft, behauptet für sich allein keine Tensorprüfung oder Vergleichsfreigabe. Der Rootvalidator prüft tatsächlich Q/Target/Adam und erneutes Laden. Historische Abnahme erst nach vollständig beendetem Supervisor mit vier Exit0-Jobs, leeren active/queue und allen vier Receipts. Trainingsreceipts bleiben `eligible=False`; nur die separate historische Abnahme setzt `eligible_for_comparison=True`.

Die gehashte Abnahme bindet die Originalquellenidentität, globale/lokale Vorbereitungsmanifeste, vier Startgewichte, Supervisorstart und -abschluss, beide Paarfreigaben, unabhängigen Audit, Rootvalidator sowie V14 und ZIP. Je Arm sind Receipt und sämtliche neun Artefakte erforderlich: `weights/agent.pth`, `weights/agent.buffer.npz`, `rollouts.jsonl`, `validation_games.jsonl`, `training_audit.json`, `train.csv`, `prefill_proof.json`, `prefill_bundle.json`, `prefill_events.jsonl`. Fehlende Dateien bleiben auch nach Übertragung in einen anderen Checkout ein Fehler. Historische Laufzeit-/Quellenmetadaten werden erhalten; ein späterer Vergleichs-HEAD macht sie nicht zur aktuellen Quelle. Abnahmehash im Adapter vor Ausführung fest pinnen; der Stagingwert `None` sperrt die Montage ausdrücklich.

Die Replaybuffer sind je ungefähr187MB groß und bleiben ausdrücklich außerhalb von Git. Modelle und kompakte Rohdaten werden versioniert; ein Pull allein liefert deshalb keine vollständige Roh-Audit-Reproduktion in Mahmouds oder einem anderen Checkout. Dafür müssen die originalen Buffer separat übertragen und anhand ihrer angenommenen Hashes geprüft werden. Pfadrebasing ersetzt diese Übertragung nicht; der Leser weist fehlende Buffer weiterhin ab.

Genau drei Rollen:

- V14: die 36 ursprünglichen Netze in ihrer unveränderten Reihenfolge.
- CONTROL38: V14 plus finale Q-Netze control43 und control44 in dieser Reihenfolge.
- ALIGNED38: V14 plus finale Q-Netze aligned43 und aligned44 in dieser Reihenfolge.

Alle 38 Netze erhalten dasselbe Gewicht. Keine Zwischencheckpoint-/Mitgliedersuche. Beide Kandidaten erhalten exakt die ursprüngliche effektive V14-Inferenzkonfiguration, insbesondere `art_splash_in_training=False` und `fog_unknown_reward_neutral=False`. Die angenommenen Einzelnetze müssen die ursprüngliche Trainingskonfiguration mit ausschließlich rollenabhängigem Artillerieflag erfüllen. Strikte Zustandsladung, endliche Tensoren, 79er Eingaben, unveränderte Originalmitglieder, veränderte finale Netze und erneutes Laden werden geprüft. Montage schreibt ausschließlich in einen neuen Experimentordner, niemals in Abgabegewichte.

## Vier feste Kartenlisten

Jede Liste enthält genau die hier genannten 20 Ganzzahlen in aufsteigender Reihenfolge. Beide Seiten werden gespielt.

| Liste | Festgelegte Karten |
| --- | --- |
| selection_panel | 9800000, 9800001, 9800002, 9800003, 9800004, 9800005, 9800006, 9800007, 9800008, 9800009, 9800010, 9800011, 9800012, 9800013, 9800014, 9800015, 9800016, 9800017, 9800018, 9800019 |
| selection_direct | 9800100, 9800101, 9800102, 9800103, 9800104, 9800105, 9800106, 9800107, 9800108, 9800109, 9800110, 9800111, 9800112, 9800113, 9800114, 9800115, 9800116, 9800117, 9800118, 9800119 |
| confirmation_panel | 9801000, 9801001, 9801002, 9801003, 9801004, 9801005, 9801006, 9801007, 9801008, 9801009, 9801010, 9801011, 9801012, 9801013, 9801014, 9801015, 9801016, 9801017, 9801018, 9801019 |
| confirmation_direct | 9801100, 9801101, 9801102, 9801103, 9801104, 9801105, 9801106, 9801107, 9801108, 9801109, 9801110, 9801111, 9801112, 9801113, 9801114, 9801115, 9801116, 9801117, 9801118, 9801119 |

Diese Zahlen sind vorab festgelegt, ihre endgültige Frischeabnahme steht bei Erstellung dieser Spezifikation noch aus. Die vorläufige Suche fand keine beobachtete Überschneidung; unbekannte seedlose/uneindeutige Datensätze und externe Läufe verhindern eine absolute Frischegarantie. Vor jedem Leistungsspiel erneuten zielbezogenen Rohdatenaudit ausführen, bekannte Lücken benennen und Root-Abnahme archivieren. `seed_acceptance.json` bindet exakt diese vier Listen und den Rootbericht; dieser bindet Rohdatenaudit und gegebenenfalls zusätzliche Belegdateien. Sein Urteil lautet `PASS`, `no_observed_conflicts=True` mit ausdrücklich dokumentierten `limitations`. Tatsächlichen Hash fest im Adapter pinnen; `None` oder fehlende/manipulierte Belege sperren den Start. Bei Konflikt keine stille Umnummerierung.

## Auswahl: genau 440 Spiele

V14, CONTROL38 und ALIGNED38 gegen Solution92, sol92_sq und default: 3×3×20×2=360 Spiele. Beide Kandidaten zusätzlich gegen V14 auf den getrennten Direktkarten: 2×20×2=80. Elf Jobs mit jeweils 40 vollständigen Spielen. Beide Kandidaten sind nominierbar.

Alle fünf Bedingungen müssen gelten:

1. Im Zweierpanel Solution92/sol92_sq mindestens +2,5 Prozentpunkte Score gegenüber V14; exakt mindestens vier zusätzliche Halbsieg-Einheiten aus 80 Spielen.
2. Solution-Score mindestens V14.
3. Strikte Solution-Siege mindestens V14.
4. default 40/40 strikte Siege.
5. Direktspielscore mindestens 50 %, also mindestens 40 Halbsieg-Einheiten aus 40 Spielen.

Unter Qualifizierten höchster Panelscore, dann meiste strikte Solution-Siege, dann höchster Direktspielscore; vollständiger Gleichstand zugunsten CONTROL38. Genau ein Nominierter oder keiner. ALIGNED−CONTROL wird zusätzlich gepaart beschrieben; zwei Trainingsstarts erlauben keinen isolierten Mechanismusnachweis. Ganze Auswahl inklusive aller Rohdaten/Receipts unabhängig akzeptieren und unverändert nachrechnen, bevor der Bestätigungsplan erzeugt wird.

## Bestätigung: genau 600 Spiele

Nur Nominierter und V14 gegen LOCAL_SIX plus default: 2×7×20×2=560 Spiele. LOCAL_SIX ist ausdrücklich Solution92, sol92_sq, V3, V7, V10, V13; nicht das abweichende BATTLE_SIX. Nur Nominierter direkt gegen V14 auf getrennten Karten: 40 Spiele. Fünfzehn Jobs, Panel je Modell 240 Spiele. Keine dritte Rolle.

Alle sieben unveränderten Gates aus `league_gates.confirm_checks(..., panel=LOCAL_SIX, min_delta=.01)`:

1. Sechserpanel-Scoregewinn mindestens +1 pp.
2. Untere 95%-Grenze des Panelgewinns strikt über null.
3. Solution-Scoreänderung mindestens −0,5 pp.
4. Untere Solution-Grenze strikt über −2,5 pp.
5. Defaultscore mindestens 99 %.
6. Defaultscoreänderung mindestens −1 pp.
7. Untere Direktspielscoregrenze strikt über 50 %.

Dazu drei Schutzbedingungen: Solution-Score mindestens V14, strikte Solution-Siege mindestens V14, default mindestens 99 % strikte Siege. Hier erfordert Letzteres 40/40 Siege. Ein einzelnes Default-Remis verfehlt das Gate. Alle zehn müssen bestehen; bestanden bedeutet noch keine Promotion.

## Statistik, Grenzen und Betrieb

Score=(strikte Siege+0,5×Remis)/Spiele; W/D/L und strikte Siege getrennt. Vollständige Karten-/Seiten-/Gegnerschlüssel, CSV- und Receiptmatrix, Originalbefehle und Eingangsbindung werden vor jeder Statistik erzwungen. Ganze Karten mit beiden Seiten und allen Panelgegnern gepaart resampeln: 5000 Ziehungen, PCG64-Seed0, 95%-Perzentile. Phasen getrennt auswerten. Nur 20 unabhängige Kartencluster je Liste; gegenüber 40 bei ähnlicher Streuung näherungsweise √2 größere Standardfehler. Keine Powergarantie oder simultane Intervallgarantie, kein Nachschlag bei Unklarheit.

Quellen/HEAD, Modelle, Gegner, alle vier Listen, Spec, Plan und Größenvermerk bleiben von Auswahlstart bis Ende einer eventuellen Bestätigung unverändert. Auditcode währenddessen außerhalb des Repositorys. Maximal zwei Modellworker, keine parallelen Tests, Netzstrom, frische Kontingentfreigabe und strikt unter 100 % Nutzung, kanonischer eigener STOP, gemeinsamer Rechenlock, Erkennung fremder Prozesse und ausschließlich eigenes Cleanup. Einmalige Ausgaben und Startreservierungen; kein Resume. FAILED/unklar/kein Nominierter beendet die Welle. Eine Übernahme erfordert anschließend unabhängige Datenabnahme, V14-Sicherung, Kurs-/Lade-/Laufzeitprüfung und Reproduktion.
