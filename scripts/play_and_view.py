"""Ein Spiel ueber den unveraenderten Kurs-Runner spielen und sofort im Browser ansehen.

    .venv/bin/python -m scripts.play_and_view                    # Sherlock gegen Solution_92
    .venv/bin/python -m scripts.play_and_view --gegner default   # gegen default (oder dqn)
    .venv/bin/python -m scripts.play_and_view --seite 1          # Sherlock als player_1

Der Kurs-Runner (`lux/runner.py`, train=False) speichert das Replay als JSON. Dieses Skript
verpackt es wie `luxai-s3 ... --output replay.html` in eine HTML-Datei mit dem offiziellen
Viewer (https://s3vis.lux-ai.org, braucht Internet) und oeffnet sie im Standardbrowser.
Kein Training, keine Gewichte geschrieben; die HTML-Dateien bleiben unter `replays/`.
Die Demo-Seite (`scripts/demo_server.py`) ruft dieses Skript mit `--json` auf.
"""
from __future__ import annotations

import argparse
import json
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHERLOCK = 15  # Gruppe in Paths.csv
GEGNER = {"default": 1, "solution": 2, "dqn": 3}
VIEWER = "https://s3vis.lux-ai.org"


def replay_html(replay: dict) -> str:
    """HTML wie in `luxai_runner/episode.py`: Replay eingebettet, Viewer-Skript von s3vis."""
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="{VIEWER}/eye.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lux Eye S3</title>
    <script>
window.episode = {json.dumps(replay)};
    </script>
    <script type="module" crossorigin src="{VIEWER}/index.js"></script>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""


def match_wins(replay: dict, sherlock: str) -> tuple[int, int]:
    """Gewonnene Matches (Sherlock, Gegner) laut letzter Beobachtung."""
    wins = replay["observations"][-1]["team_wins"]
    i = 0 if sherlock == "player_0" else 1
    return int(wins[i]), int(wins[1 - i])


def match_sequence(replay: dict, sherlock: str) -> list[bool | None]:
    """Sieger je Match in Spielreihenfolge: True = Sherlock, False = Gegner, None = unklar."""
    i = 0 if sherlock == "player_0" else 1
    seq, prev = [], [0, 0]
    for obs in replay["observations"]:
        wins = [int(w) for w in obs["team_wins"]]
        gained = [wins[0] - prev[0], wins[1] - prev[1]]
        if gained != [0, 0]:
            seq.append(None if gained[0] == gained[1] else gained[i] > gained[1 - i])
        prev = wins
    return seq


def play(gegner: str, seite: int) -> dict:
    """Ein Spiel ueber den Kurs-Runner; schreibt die HTML-Datei und liefert die Zusammenfassung."""
    from lux.runner import run_agents  # erst hier: --help bleibt schnell

    p0, p1 = (SHERLOCK, GEGNER[gegner]) if seite == 0 else (GEGNER[gegner], SHERLOCK)
    run_agents(p0, p1, games_to_play=1, train=False)

    folder = ROOT / "replays" / f"{p0}_vs_{p1}"
    replay = json.loads((folder / "episode_0.json").read_text(encoding="utf-8"))
    sherlock, other = f"player_{seite}", f"player_{1 - seite}"
    ours, theirs = match_wins(replay, sherlock)
    now = datetime.now()
    out = folder / f"{now:%Y%m%d_%H%M%S}_sherlock_vs_{gegner}.html"
    out.write_text(replay_html(replay), encoding="utf-8")
    meta = replay.get("metadata", {})
    return {
        "gegner": gegner,
        "gegner_name": meta.get("players", {}).get(other, gegner),
        "seite": seite,
        "sherlock": sherlock,
        "seed": meta.get("seed"),
        "ours": ours,
        "theirs": theirs,
        "matches": match_sequence(replay, sherlock),
        "html": out.relative_to(ROOT).as_posix(),
        "datum": f"{now:%Y-%m-%d}",
        "zeit": f"{now:%H:%M}",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gegner", choices=sorted(GEGNER), default="solution")
    ap.add_argument("--seite", type=int, choices=(0, 1), default=0, help="Sherlock als player_0 oder player_1")
    ap.add_argument("--no-open", action="store_true", help="HTML nur speichern, nicht im Browser oeffnen")
    ap.add_argument("--json", action="store_true", help="Zusammenfassung zusaetzlich als letzte Zeile in JSON")
    args = ap.parse_args()

    game = play(args.gegner, args.seite)
    out = ROOT / game["html"]
    verdict = "gewinnt" if game["ours"] > game["theirs"] else "verliert"
    print(f"Sherlock ({game['sherlock']}) {verdict} {game['ours']}:{game['theirs']} Matches "
          f"gegen {game['gegner_name']} (Seed {game['seed']}).")
    print(f"Visualisierung: {out}")
    if args.json:
        print(json.dumps(game, ensure_ascii=False))
    if not args.no_open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
