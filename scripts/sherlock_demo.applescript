-- Sherlock Demo (22.10.2026): Doppelklick-App fuer die Live-Demo.
-- Startet die lokale Demo-Seite (scripts/demo_server.py) und oeffnet sie im Browser. Dort Gegner und
-- Seite waehlen; das Spiel laeuft ueber den Kurs-Runner und erscheint direkt im Lux-Viewer.
-- Falls die Seite nicht startet: Rueckfall mit einfachen Dialogen (scripts/play_and_view.py).
-- Bauen (aus dem Projektordner): sh scripts/build_demo_app.sh

on run
	set projectDir to my projektOrdner()
	if not my demoLaeuft() then
		-- nur der Server laeuft im Hintergrund (mit ";" statt "&&", alle Kanaele umgeleitet),
		-- sonst wartet do shell script, bis der Server endet
		do shell script "cd " & quoted form of projectDir & " || exit 1; mkdir -p replays; nohup .venv/bin/python -m scripts.demo_server --port " & my demoPort() & " > replays/demo_server.log 2>&1 < /dev/null &"
		repeat 40 times -- bis zu 20 Sekunden
			delay 0.5
			if my demoLaeuft() then exit repeat
		end repeat
	end if
	if my demoLaeuft() then
		open location "http://127.0.0.1:" & my demoPort() & "/"
	else
		set protokoll to do shell script "tail -n 12 " & quoted form of (projectDir & "/replays/demo_server.log") & " 2>/dev/null; true"
		set wahl to button returned of (display dialog "Die Demo-Seite konnte nicht gestartet werden." & return & return & protokoll buttons {"Abbrechen", "Ohne Seite spielen"} default button "Ohne Seite spielen" with title "Sherlock Demo" with icon caution)
		if wahl is "Ohne Seite spielen" then my ohneSeite(projectDir)
	end if
end run

on demoPort()
	return "8615"
end demoPort

on projektOrdner()
	-- neben der App, eine Ebene hoeher (Quelltext in scripts/) oder der Standardpfad
	set appPath to POSIX path of (path to me)
	return do shell script "d=$(dirname " & quoted form of appPath & "); if [ -f \"$d/scripts/demo_server.py\" ]; then echo \"$d\"; elif [ -f \"$(dirname \"$d\")/scripts/demo_server.py\" ]; then dirname \"$d\"; else echo \"$HOME/Documents/AKI_LuxAgent15\"; fi"
end projektOrdner

on demoLaeuft()
	try
		do shell script "curl -s -m 1 http://127.0.0.1:" & my demoPort() & "/api/ping | grep -q '\"ok\": true'"
		return true
	on error
		return false
	end try
end demoLaeuft

on ohneSeite(projectDir)
	repeat
		set wahl to button returned of (display dialog "Gegen wen soll Sherlock spielen?" buttons {"default", "Prof-DQN", "Solution_92"} default button "Solution_92" with title "Sherlock Demo")
		if wahl is "default" then
			set gegner to "default"
		else if wahl is "Prof-DQN" then
			set gegner to "dqn"
		else
			set gegner to "solution"
		end if
		try
			set ausgabe to do shell script "cd " & quoted form of projectDir & " && .venv/bin/python -m scripts.play_and_view --no-open --gegner " & gegner & " 2>&1"
		on error fehler
			display dialog "Das Spiel konnte nicht gestartet werden:" & return & return & fehler buttons {"OK"} default button "OK" with title "Sherlock Demo" with icon stop
			return
		end try
		set ergebnis to "Spiel beendet."
		set datei to ""
		repeat with zeile in paragraphs of ausgabe
			set zeile to zeile as text
			if zeile starts with "Sherlock (" then set ergebnis to zeile
			if zeile starts with "Visualisierung: " then set datei to text 17 thru -1 of zeile
		end repeat
		if datei is not "" then do shell script "open " & quoted form of datei
		set weiter to button returned of (display dialog ergebnis & return & return & "Das Spiel ist im Browser geöffnet. Dort auf ▶ klicken." buttons {"Fertig", "Nochmal"} default button "Fertig" with title "Sherlock Demo")
		if weiter is "Fertig" then exit repeat
	end repeat
end ohneSeite
