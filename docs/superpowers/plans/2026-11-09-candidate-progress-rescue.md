# Fortschrittsabhängige Kandidatenrettung

## Ziel und feste Hypothese

Die reproduzierte V14-Niederlage 9946007/player_0 zeigt Kandidaten ab Schritt 44, danach bis einschließlich Aktion 75 keinen weiteren Eintritt in zuvor bekannte Kandidaten und eigene Punkte erst ab 81. Das belegt keine alleinige Ursache. Die pauschale Vorverlegung von `rescue_after` und die HOLD-Studien bleiben geschlossen. Dieser einzelne neue Versuch prüft, ob die vorhandene Kandidatenrettung bei öffentlich beobachtetem Stillstand früher helfen kann.

Ein einziger opt-in-Schalter `cand_stall_rescue=False` ergänzt den bisherigen Core. Keine neuen Netze, Gewichte, Rewards, Ziele oder Masken. V14 behält seinen Defaultpfad; die Abgabe und ZIP werden nicht geändert. Der alte globale `cand_rescue`-Fallback nach 30 Schritten bleibt unverändert, ebenso `zone_rescue`.

## Exakte Bedingung

- Nur Auswertung, `cand_rescue=True`, Matchindex 0, mindestens ein bekanntes Relic und Kandidaten, noch kein bestätigtes Punktfeld.
- Öffentlichen Fortschritt einmal pro neuem Beobachtungsschritt erfassen. Fortschritt ist eine eigene Einheit mit nichtnegativer Energie auf der **kopierten vorherigen Kandidatenmaske**, positiver eigener Punktgewinn, neue Relicinformation oder neu gesetzte Punkt-/Nichtpunktklassifikation des Beliefs. Auch fortgesetzte Kandidatenbesetzung zählt konservativ als Fortschritt.
- Nach Fortschritt Zähler 0; erst nach zwölf vollständig beobachteten aufeinanderfolgenden Übergängen ohne Fortschritt frühe Rettung. Diese feste Schwelle wird nicht anhand der Ergebnisse angepasst.
- Spiel-/Seiten-/Matchwechsel, fehlende oder rückläufige Schritte und Wissensrücknahmen setzen konservativ zurück. Keine rückwirkende Anrechnung der Zeit vor bekannten Relics/Kandidaten. Gleiche Beobachtung nicht mehrfach zählen; keine Einheiten und Matchreset dürfen keine erfundenen Übergänge erzeugen.
- Die neue Frührettung gilt nur für eine Einheit mit einem aktuell gültigen Kandidatenziel. Alte globale Rettung bleibt unabhängig davon wahr. Nur öffentliche Informationen; keine Engine-Wahrheit oder zukünftige Beobachtung.
- Der bestehende Rescue-Hook beeinflusst neben Zieltreue/Annäherung auch Nebelausnahmen. Das kann Energie kosten und schlechter spielen. Spätere Regeln bleiben erhalten; tatsächliche finale Aktionen und Ergebnisse entscheiden.

## Umsetzung und technische Prüfung

1. Minimale Zustandslogik und Default-false-Config; gezielte synthetische Tests für Zeitgrenze, mutable Masken, Informationsgewinn/Rücknahme, Seiten/Match/Gaps, Training/OFF, Zielbindung und unveränderten globalen Fallback. Keine breite alte Suite wiederholen.
2. Unabhängiger Review. Vor realen Spielen geprüfte Quelle committen und einfrieren. Maximal zwei Modellworker, keine gleichzeitigen Tests; Akku ausdrücklich erlaubt, echte frische Quota prüfen, keine Resets durch Codex.
3. Zwei reine Evalkopien OFF/ON mit genau den unveränderten 36 V14-Mitgliedern in gleicher Reihenfolge und identischen Tensorbytes. Konfiguration nur `frozen=False` sowie OFF/ON-Schalter verschieden. Beide Abgabegewichte und ZIP per Hash geschützt.
4. Genau vier bekannte Technikspiele: OFF und ON jeweils 9946007/player_0 und 831006/player_1. OFF muss native Aktionshashes und Resultate des archivierten V14 reproduzieren. ON muss mindestens eine tatsächliche frühe zielgebundene Rettung und eine veränderte finale Aktionsfolge zeigen. Keine Ersatzkarte oder automatischer Neustart. Auch OFF/ON-Gewichte nach Spielen exakt prüfen. Technikergebnisse sind keine Stärkeprüfung.

## Fester kleiner Vergleich nach tatsächlicher Technikabnahme

Profil `candidate_progress_20261109`. Vor Aufnahme einmaliger begrenzter lokaler Kartenkonfliktcheck; Grenzen dokumentieren.

- Solution: Karten 9948000–9948019, beide Spielseiten; OFF 40 und ON 40 vollständige Spiele.
- Direkt: Karten 9948100–9948119, beide Spielseiten; ON gegen OFF 40 vollständige Spiele.
- Insgesamt 120 Leistungsspiele, drei Jobs in zwei Wellen (2 + 1), separater Root-Start nach Technikabnahme. Keine Gradienten, Zwischenauswahl, Schwellenanpassung, Ersatzspiele oder automatische Verlängerung.
- Vorab feste Nominierung: tatsächliche ON-Siege gegen Solution mindestens so viele wie OFF; direkt mindestens 24 von 40 tatsächliche Siege. Unentschieden zählen nicht als Sieg. Vollständige Daten, korrekte Matchwertung, keine Agentenfehler erforderlich. Scoreintervalle zählen Remis als 0,5, resampeln ganze Karten einschließlich beider Seiten, 5.000 PCG64-Seed-0-Ziehungen; deskriptiv ohne Korrektur für die vielen bisherigen Versuche.
- Fehlschlag schließt diese Variante ohne Nachschlag. Bestehen erlaubt nur eine separat vorab festgelegte frische Bestätigung, keinen direkten V14-Ersatz. Danach gegebenenfalls Kursprüfung, Sicherung und belegter Vorteil für eine Übernahme.

## Übergabe

Root koordiniert getrennte Schreibbereiche, prüft tatsächliche Ergebnisse und aktualisiert Arbeitsstand/Experimentprotokoll für Mahmoud. Werkzeuge und abgeschlossene Ergebnisse sinnvoll getrennt committen und nach sicherem Remote-Abgleich pushen; primäre Arbeitskopie verlustfrei aktualisieren. Rohdaten bytegleich archivieren, CSV-Attribute vor Aufnahme setzen. Geschlossene Studien nicht erneut starten.
