-- Sherlock Demo (22.10.2026): Doppelklick-App fuer die Live-Demo.
-- Spielt ein Spiel ueber den Kurs-Runner (scripts/play_and_view.py) und oeffnet das Replay im Lux-Viewer.
-- Bauen (aus dem Projektordner): osacompile -o "Sherlock Demo.app" scripts/sherlock_demo.applescript

on run
	set appPath to POSIX path of (path to me)
	-- Projektordner: neben der App, eine Ebene hoeher (Quelltext in scripts/) oder der Standardpfad
	set projectDir to do shell script "d=$(dirname " & quoted form of appPath & "); if [ -f \"$d/scripts/play_and_view.py\" ]; then echo \"$d\"; elif [ -f \"$(dirname \"$d\")/scripts/play_and_view.py\" ]; then dirname \"$d\"; else echo \"$HOME/Documents/AKI_LuxAgent15\"; fi"
	repeat
		set wahl to button returned of (display dialog "Gegen wen soll Sherlock spielen?" buttons {"default", "Prof-DQN", "Solution_92"} default button "Solution_92" with title "Sherlock Demo")
		if wahl is "default" then
			set gegner to "default"
		else if wahl is "Prof-DQN" then
			set gegner to "dqn"
		else
			set gegner to "solution"
		end if
		display notification "Spiel läuft, etwa 10 Sekunden …" with title "Sherlock Demo"
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
end run
